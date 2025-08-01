import streamlit as st
import pandas as pd
import re
import os
import io

# --- การตั้งค่าไฟล์สำหรับเก็บข้อมูล ---
# ไฟล์สำหรับเก็บเบอร์โทรศัพท์ทั้งหมดที่เคยบันทึก
COMBINED_NUMBERS_FILE = 'combined_numbers.txt'
# ไฟล์สำหรับเก็บชื่อไฟล์ที่เคยบันทึกข้อมูลไปแล้ว
UPLOADED_FILES_LOG = 'uploaded_files_log.txt'

# --- ฟังก์ชันช่วยทำงาน ---
def normalize_phone_number(number_str):
    """
    แปลงเบอร์โทรศัพท์ให้อยู่ในรูปแบบ 10 หลัก (08XXXXXXXX)
    """
    if isinstance(number_str, (int, float)):
        number_str = str(int(number_str))
    
    if not isinstance(number_str, str):
        return None

    # ลบอักขระที่ไม่ใช่ตัวเลข
    digits = re.sub(r'\D', '', number_str)

    # จัดการรูปแบบเบอร์ที่พบบ่อย
    if digits.startswith('66') and len(digits) >= 11:
        digits = '0' + digits[2:]
    elif len(digits) == 9 and digits.startswith(('6', '8', '9')):
        digits = '0' + digits
    
    # ตรวจสอบว่าเป็นเบอร์โทรศัพท์มือถือ 10 หลักหรือไม่
    if len(digits) == 10 and digits.startswith('0'):
        return digits
    return None

def get_all_numbers_from_file(filepath):
    """
    ดึงเบอร์โทรศัพท์ทั้งหมดจากไฟล์ที่กำหนด
    """
    numbers = set()
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                numbers.add(line.strip())
    return numbers

def insert_numbers_to_file(numbers):
    """
    เพิ่มเบอร์ใหม่ลงในไฟล์รวมเบอร์
    """
    new_numbers_count = 0
    try:
        with open(COMBINED_NUMBERS_FILE, 'a', encoding='utf-8') as f:
            for number in numbers:
                f.write(number + '\n')
                new_numbers_count += 1
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: ไม่สามารถเขียนไฟล์ได้: {e}")
    return new_numbers_count

def check_file_uploaded_before(filename):
    """
    ตรวจสอบว่าไฟล์นี้เคยถูกบันทึกไปแล้วหรือไม่ โดยดูจากไฟล์บันทึก
    """
    uploaded_files = get_all_numbers_from_file(UPLOADED_FILES_LOG)
    return filename in uploaded_files

def record_uploaded_file(filename):
    """
    บันทึกชื่อไฟล์ว่าเคยถูกอัปโหลดและบันทึกแล้ว
    """
    try:
        with open(UPLOADED_FILES_LOG, 'a', encoding='utf-8') as f:
            f.write(filename + '\n')
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: ไม่สามารถเขียนไฟล์บันทึกได้: {e}")

# --- ตั้งค่า Session State สำหรับ Streamlit ---
if 'processed_numbers_from_file' not in st.session_state:
    st.session_state.processed_numbers_from_file = set()
if 'new_numbers_to_add' not in st.session_state:
    st.session_state.new_numbers_to_add = set()
if 'duplicates_found' not in st.session_state:
    st.session_state.duplicates_found = set()
if 'combined_numbers' not in st.session_state:
    st.session_state.combined_numbers = get_all_numbers_from_file(COMBINED_NUMBERS_FILE)
if 'status_message' not in st.session_state:
    st.session_state.status_message = ["ยินดีต้อนรับสู่โปรแกรมจัดการเบอร์โทรศัพท์!"]

def update_status(message):
    st.session_state.status_message.append(message)

# --- ส่วนติดต่อผู้ใช้ (Streamlit UI) ---
st.set_page_config(
    page_title="SMS Marketing Number Manager",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
    .reportview-container .main .block-container{
        max-width: 1000px;
        padding-top: 2rem;
        padding-right: 2rem;
        padding-left: 2rem;
        padding-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        font-family: 'Kanit';
    }
    h1, h2, h3, h4, h5, h6, .st-font {
        font-family: 'Kanit';
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("โปรแกรมจัดการเบอร์โทรศัพท์สำหรับ SMS Marketing")

# แสดงจำนวนเบอร์ในไฟล์รวม
st.info(f"**จำนวนเบอร์ในไฟล์รวมเบอร์: {len(st.session_state.combined_numbers)} เบอร์**")

# อัปโหลดไฟล์
st.markdown("### 1. อัปโหลดไฟล์เบอร์โทรศัพท์")
uploaded_files = st.file_uploader(
    "เลือกไฟล์เบอร์ (.txt หรือ .xlsx)",
    type=['txt', 'xlsx'],
    accept_multiple_files=True,
    help="สามารถเลือกได้หลายไฟล์พร้อมกัน"
)

# ปุ่มประมวลผล
if st.button("ประมวลผลไฟล์"):
    if uploaded_files:
        st.session_state.processed_numbers_from_file.clear()
        st.session_state.new_numbers_to_add.clear()
        st.session_state.duplicates_found.clear()
        
        all_numbers_from_files = set()
        
        for uploaded_file in uploaded_files:
            filename = uploaded_file.name
            update_status(f"กำลังประมวลผลไฟล์: {filename}")
            
            try:
                numbers_from_file = set()
                if filename.endswith('.txt'):
                    lines = uploaded_file.read().decode('utf-8').splitlines()
                    for line in lines:
                        num = normalize_phone_number(line.strip())
                        if num:
                            numbers_from_file.add(num)
                elif filename.endswith('.xlsx'):
                    df = pd.read_excel(uploaded_file, engine='openpyxl')
                    column_name = df.columns[0]
                    for col in df.columns:
                        if 'phone' in str(col).lower() or 'number' in str(col).lower():
                            column_name = col
                            break
                    for num_raw in df[column_name].dropna():
                        num = normalize_phone_number(num_raw)
                        if num:
                            numbers_from_file.add(num)
                
                all_numbers_from_files.update(numbers_from_file)
                
            except Exception as e:
                st.error(f"ข้อผิดพลาดในการประมวลผลไฟล์ {filename}: {e}")
        
        st.session_state.processed_numbers_from_file = all_numbers_from_files
        
        # คำนวณเบอร์ที่สามารถใช้ได้และเบอร์ที่ซ้ำ
        st.session_state.combined_numbers = get_all_numbers_from_file(COMBINED_NUMBERS_FILE)
        st.session_state.new_numbers_to_add = st.session_state.processed_numbers_from_file - st.session_state.combined_numbers
        st.session_state.duplicates_found = st.session_state.processed_numbers_from_file.intersection(st.session_state.combined_numbers)
        
        update_status(f"ประมวลผลไฟล์ทั้งหมดสำเร็จ")
        update_status(f"พบเบอร์โทรศัพท์ทั้งหมด (หลังลบซ้ำ): {len(st.session_state.processed_numbers_from_file)} เบอร์")
        update_status(f"**เบอร์ที่สามารถใช้ส่ง SMS ได้ (เบอร์ใหม่): {len(st.session_state.new_numbers_to_add)} เบอร์**")
        
        st.success("ประมวลผลสำเร็จ!")
        
    else:
        st.warning("โปรดอัปโหลดไฟล์เบอร์โทรศัพท์ก่อน")

# แสดงผลลัพธ์
st.markdown("---")
st.markdown("### 2. ผลลัพธ์และตัวเลือกการดำเนินการ")
col1, col2 = st.columns(2)

with col1:
    st.info("#### ข้อมูลสถานะ")
    status_area = st.empty()
    status_area.markdown("\n".join(st.session_state.status_message))
    
    st.markdown("---")
    st.info("#### เบอร์ที่สามารถใช้ส่ง SMS ได้ (เบอร์ใหม่)")
    if st.session_state.new_numbers_to_add:
        st.text("\n".join(list(st.session_state.new_numbers_to_add)[:50]))
        if len(st.session_state.new_numbers_to_add) > 50:
            st.text("...")
    else:
        st.text("ไม่มีเบอร์ใหม่")

with col2:
    st.success("#### บันทึกและส่งออก")
    
    if st.button("บันทึกลงไฟล์รวมเบอร์"):
        if not st.session_state.processed_numbers_from_file:
            st.warning("โปรดประมวลผลไฟล์ก่อนบันทึก")
        else:
            already_uploaded = [f.name for f in uploaded_files if check_file_uploaded_before(f.name)]
            if already_uploaded:
                if st.warning(f"ไฟล์เหล่านี้เคยถูกบันทึกแล้ว: {', '.join(already_uploaded)} คุณต้องการบันทึกต่อหรือไม่?"):
                    st.stop()
            
            new_count = insert_numbers_to_file(st.session_state.new_numbers_to_add)
            for f in uploaded_files:
                record_uploaded_file(f.name)
            
            st.session_state.combined_numbers = get_all_numbers_from_file(COMBINED_NUMBERS_FILE)
            update_status(f"บันทึกเบอร์ใหม่ {new_count} เบอร์")
            update_status(f"จำนวนเบอร์ในไฟล์รวมเบอร์: {len(st.session_state.combined_numbers)} เบอร์")
            st.success(f"บันทึกสำเร็จ! เพิ่มเบอร์ใหม่ {new_count} เบอร์")

    def create_export_file(numbers_set, file_format):
        if file_format == 'txt':
            return "\n".join(sorted(list(numbers_set))).encode('utf-8')
        elif file_format == 'xlsx':
            df = pd.DataFrame(sorted(list(numbers_set)), columns=["Phone Number"])
            output = io.BytesIO()
            df.to_excel(output, index=False)
            return output.getvalue()
    
    st.markdown("---")
    export_format = st.radio("เลือกรูปแบบไฟล์ส่งออก", ['txt', 'xlsx'], horizontal=True)

    if st.session_state.new_numbers_to_add:
        st.download_button(
            label=f"ดาวน์โหลดเบอร์ใหม่ ({len(st.session_state.new_numbers_to_add)} เบอร์)",
            data=create_export_file(st.session_state.new_numbers_to_add, export_format),
            file_name=f"new_numbers.{export_format}",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if export_format == 'xlsx' else "text/plain"
        )
    if st.session_state.duplicates_found:
        st.download_button(
            label=f"ดาวน์โหลดเบอร์ที่ซ้ำ ({len(st.session_state.duplicates_found)} เบอร์)",
            data=create_export_file(st.session_state.duplicates_found, export_format),
            file_name=f"duplicate_numbers.{export_format}",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if export_format == 'xlsx' else "text/plain"
        )
    if st.session_state.combined_numbers:
        st.download_button(
            label=f"ดาวน์โหลดเบอร์ทั้งหมดในไฟล์รวมเบอร์ ({len(st.session_state.combined_numbers)} เบอร์)",
            data=create_export_file(st.session_state.combined_numbers, export_format),
            file_name=f"all_combined_numbers.{export_format}",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if export_format == 'xlsx' else "text/plain"
        )

st.markdown("---")
if st.button("ล้างไฟล์รวมเบอร์"):
    if st.warning("คุณแน่ใจหรือไม่ว่าต้องการลบเบอร์ทั้งหมดในไฟล์รวมเบอร์? การดำเนินการนี้ไม่สามารถย้อนกลับได้!"):
        try:
            with open(COMBINED_NUMBERS_FILE, 'w', encoding='utf-8') as f:
                f.write("")
            with open(UPLOADED_FILES_LOG, 'w', encoding='utf-8') as f:
                f.write("")
            st.session_state.combined_numbers = set()
            st.success("ลบเบอร์ในไฟล์รวมเบอร์ทั้งหมดเรียบร้อยแล้ว")
            st.session_state.status_message.append("ไฟล์รวมเบอร์ถูกลบแล้ว")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"ข้อผิดพลาดในการลบ: {e}")

