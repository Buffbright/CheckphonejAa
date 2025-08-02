import streamlit as st
import pandas as pd
import re
import os
import io

# --- การตั้งค่าไฟล์สำหรับเก็บข้อมูล ---
COMBINED_NUMBERS_FILE = 'combined_numbers.txt'
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

def hide_last_four_digits(number):
    """ซ่อนเลขท้าย 4 ตัวของเบอร์โทรศัพท์"""
    if len(number) > 4:
        return number[:-4] + "XXXX"
    return "XXXX"

def create_export_file(numbers_set, file_format):
    if file_format == 'txt':
        return "\n".join(sorted(list(numbers_set))).encode('utf-8')
    elif file_format == 'xlsx':
        df = pd.DataFrame(sorted(list(numbers_set)), columns=["Phone Number"])
        output = io.BytesIO()
        df.to_excel(output, index=False)
        return output.getvalue()

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
if 'is_checked_only' not in st.session_state:
    st.session_state.is_checked_only = False
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []

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



### 1. อัปโหลดไฟล์เบอร์โทรศัพท์

uploaded_files = st.file_uploader(
    "เลือกไฟล์เบอร์ (.txt หรือ .xlsx)",
    type=['txt', 'xlsx'],
    accept_multiple_files=True,
    help="สามารถเลือกได้หลายไฟล์พร้อมกัน",
    key="file_uploader" # เพิ่ม key
)
if uploaded_files:
    st.session_state.uploaded_files = uploaded_files

col_upload, col_check = st.columns(2)

with col_upload:
    if st.button("ประมวลผลไฟล์", key="process_button"): # เพิ่ม key
        if st.session_state.uploaded_files:
            st.session_state.processed_numbers_from_file.clear()
            st.session_state.new_numbers_to_add.clear()
            st.session_state.duplicates_found.clear()
            st.session_state.is_checked_only = False
            
            all_numbers_from_files = set()
            
            for uploaded_file in st.session_state.uploaded_files:
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
                        # พยายามหาคอลัมน์ที่น่าจะเป็นเบอร์โทรศัพท์
                        column_name = None
                        for col in df.columns:
                            if 'phone' in str(col).lower() or 'number' in str(col).lower():
                                column_name = col
                                break
                        if column_name is None and len(df.columns) > 0: # ถ้าหาไม่เจอ ให้ใช้คอลัมน์แรก
                            column_name = df.columns[0]
                        
                        if column_name is not None:
                            for num_raw in df[column_name].dropna():
                                num = normalize_phone_number(num_raw)
                                if num:
                                    numbers_from_file.add(num)
                        else:
                            st.warning(f"ไฟล์ {filename}: ไม่พบคอลัมน์ที่เหมาะสมสำหรับเบอร์โทรศัพท์")
                    
                    all_numbers_from_files.update(numbers_from_file)
                    
                except Exception as e:
                    st.error(f"ข้อผิดพลาดในการประมวลผลไฟล์ {filename}: {e}")
            
            st.session_state.processed_numbers_from_file = all_numbers_from_files
            
            st.session_state.combined_numbers = get_all_numbers_from_file(COMBINED_NUMBERS_FILE)
            st.session_state.new_numbers_to_add = st.session_state.processed_numbers_from_file - st.session_state.combined_numbers
            st.session_state.duplicates_found = st.session_state.processed_numbers_from_file.intersection(st.session_state.combined_numbers)
            
            update_status(f"ประมวลผลไฟล์ทั้งหมดสำเร็จ")
            update_status(f"พบเบอร์โทรศัพท์ทั้งหมด (หลังลบซ้ำและกรอง): {len(st.session_state.processed_numbers_from_file)} เบอร์")
            update_status(f"**เบอร์ที่สามารถใช้ส่ง SMS ได้ (เบอร์ใหม่): {len(st.session_state.new_numbers_to_add)} เบอร์**")
            
            st.success("ประมวลผลสำเร็จ!")
            st.toast(f"ประมวลผลเบอร์โทรศัพท์จากไฟล์ทั้งหมดสำเร็จ: {len(st.session_state.processed_numbers_from_file)} เบอร์\nเบอร์ใหม่ที่ไม่ซ้ำ: {len(st.session_state.new_numbers_to_add)} เบอร์")

        else:
            st.warning("โปรดอัปโหลดไฟล์เบอร์โทรศัพท์ก่อน")

with col_check:
    if st.button("ตรวจสอบเบอร์ซ้ำ (ไม่บันทึก)", key="check_only_button"): # เพิ่ม key
        if st.session_state.uploaded_files:
            st.session_state.processed_numbers_from_file.clear()
            st.session_state.new_numbers_to_add.clear() 
            st.session_state.duplicates_found.clear()
            st.session_state.is_checked_only = True

            all_numbers_from_files = set()
            for uploaded_file in st.session_state.uploaded_files:
                filename = uploaded_file.name
                update_status(f"กำลังตรวจสอบไฟล์: {filename}")
                
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
                        column_name = None
                        for col in df.columns:
                            if 'phone' in str(col).lower() or 'number' in str(col).lower():
                                column_name = col
                                break
                        if column_name is None and len(df.columns) > 0:
                            column_name = df.columns[0]
                        
                        if column_name is not None:
                            for num_raw in df[column_name].dropna():
                                num = normalize_phone_number(num_raw)
                                if num:
                                    numbers_from_file.add(num)
                        else:
                            st.warning(f"ไฟล์ {filename}: ไม่พบคอลัมน์ที่เหมาะสมสำหรับเบอร์โทรศัพท์")

                    all_numbers_from_files.update(numbers_from_file)
                except Exception as e:
                    st.error(f"ข้อผิดพลาดในการประมวลผลไฟล์ {filename}: {e}")

            st.session_state.processed_numbers_from_file = all_numbers_from_files
            st.session_state.combined_numbers = get_all_numbers_from_file(COMBINED_NUMBERS_FILE)
            st.session_state.duplicates_found = st.session_state.processed_numbers_from_file.intersection(st.session_state.combined_numbers)
            st.session_state.new_numbers_to_add = st.session_state.processed_numbers_from_file - st.session_state.combined_numbers # Populate new_numbers_to_add even in check-only mode for download

            update_status(f"ตรวจสอบเบอร์ทั้งหมดสำเร็จ")
            if st.session_state.duplicates_found:
                update_status(f"**พบเบอร์ที่ซ้ำกับไฟล์รวมเบอร์: {len(st.session_state.duplicates_found)} เบอร์**")
                st.success("ตรวจสอบเบอร์ซ้ำสำเร็จ!")
                st.toast(f"พบเบอร์ที่ซ้ำกับไฟล์รวมเบอร์: {len(st.session_state.duplicates_found)} เบอร์")
            else:
                update_status("ไม่พบเบอร์ที่ซ้ำกับไฟล์รวมเบอร์ในไฟล์ที่อัปโหลด")
                st.success("ไม่พบเบอร์ที่ซ้ำ!")
                st.toast("ไม่พบเบอร์ที่ซ้ำกับไฟล์รวมเบอร์ในไฟล์ที่อัปโหลด")
        else:
            st.warning("โปรดอัปโหลดไฟล์เบอร์โทรศัพท์ก่อน")

### 2. ผลลัพธ์และตัวเลือกการดำเนินการ

col1, col2 = st.columns(2)

with col1:
    st.info("#### ข้อมูลสถานะ")
    for message in st.session_state.status_message:
        st.text(message)
    
    st.markdown("---")
    st.info("#### ผลลัพธ์เบอร์")
    if st.session_state.new_numbers_to_add:
        st.text_area("เบอร์ใหม่ที่สามารถใช้ได้", "\n".join([hide_last_four_digits(n) for n in list(st.session_state.new_numbers_to_add)]), height=200, key="new_numbers_display") # เพิ่ม key
    if st.session_state.duplicates_found:
        st.text_area("เบอร์ที่ซ้ำกับไฟล์รวมเบอร์", "\n".join([hide_last_four_digits(n) for n in list(st.session_state.duplicates_found)]), height=200, key="duplicates_display") # เพิ่ม key


with col2:
    st.success("#### บันทึกและส่งออก")
    
    save_password = st.text_input("รหัสผ่านสำหรับบันทึก", type="password", key='save_password_input') # แก้ไข key ให้ไม่ซ้ำ

    if st.button("บันทึกลงไฟล์รวมเบอร์", key="save_to_combined_button"): # เพิ่ม key
        if save_password == "aa123456":
            if not st.session_state.uploaded_files or st.session_state.is_checked_only:
                st.warning("โปรดประมวลผลไฟล์ก่อนบันทึก")
            else:
                already_uploaded = [f.name for f in st.session_state.uploaded_files if check_file_uploaded_before(f.name)]
                if already_uploaded:
                    st.warning(f"ไฟล์เหล่านี้เคยถูกบันทึกแล้ว: {', '.join(already_uploaded)} คุณแน่ใจหรือไม่ว่าต้องการบันทึกซ้ำ?")
                    if st.button("ยืนยันบันทึกซ้ำ", key="confirm_overwrite_button"): # เพิ่ม key สำหรับปุ่มยืนยัน
                        new_count = insert_numbers_to_file(st.session_state.new_numbers_to_add)
                        for f in st.session_state.uploaded_files:
                            record_uploaded_file(f.name)
                        
                        st.session_state.combined_numbers = get_all_numbers_from_file(COMBINED_NUMBERS_FILE)
                        update_status(f"บันทึกเบอร์ใหม่ {new_count} เบอร์")
                        update_status(f"จำนวนเบอร์ในไฟล์รวมเบอร์: {len(st.session_state.combined_numbers)} เบอร์")
                        st.success(f"บันทึกสำเร็จ! เพิ่มเบอร์ใหม่ {new_count} เบอร์")
                        st.toast(f"บันทึกเบอร์ใหม่สำเร็จ: {new_count} เบอร์")
                        st.rerun() # รีรันเพื่ออัปเดตสถานะและ UI
                    else:
                        st.stop() # หยุดการประมวลผลหากไม่ยืนยัน
                else:
                    new_count = insert_numbers_to_file(st.session_state.new_numbers_to_add)
                    for f in st.session_state.uploaded_files:
                        record_uploaded_file(f.name)
                    
                    st.session_state.combined_numbers = get_all_numbers_from_file(COMBINED_NUMBERS_FILE)
                    update_status(f"บันทึกเบอร์ใหม่ {new_count} เบอร์")
                    update_status(f"จำนวนเบอร์ในไฟล์รวมเบอร์: {len(st.session_state.combined_numbers)} เบอร์")
                    st.success(f"บันทึกสำเร็จ! เพิ่มเบอร์ใหม่ {new_count} เบอร์")
                    st.toast(f"บันทึกเบอร์ใหม่สำเร็จ: {new_count} เบอร์")
                    st.rerun() # รีรันเพื่ออัปเดตสถานะและ UI

        elif save_password != "":
            st.error("รหัสผ่านไม่ถูกต้องสำหรับการบันทึก")
        else:
            st.warning("โปรดใส่รหัสผ่านสำหรับการบันทึก")
            
    st.markdown("---")
    
    download_password = st.text_input("รหัสผ่านสำหรับดาวน์โหลด", type="password", key='download_password_input') # แก้ไข key ให้ไม่ซ้ำ
    export_format = st.radio("เลือกรูปแบบไฟล์ส่งออก", ['txt', 'xlsx'], horizontal=True, key='export_format_radio') # ย้ายขึ้นมาด้านบน

    def download_button(label, data, file_name, mime, button_key): # เพิ่ม parameter button_key
        if download_password == "aa123456":
            st.download_button(
                label=label,
                data=data,
                file_name=file_name,
                mime=mime,
                key=button_key # ใช้ key ที่ส่งเข้ามา
            )
        elif download_password != "":
            st.warning("รหัสผ่านไม่ถูกต้องสำหรับการดาวน์โหลด")

    if st.session_state.new_numbers_to_add:
        download_button(
            label=f"ดาวน์โหลดเบอร์ใหม่ ({len(st.session_state.new_numbers_to_add)} เบอร์)",
            data=create_export_file(st.session_state.new_numbers_to_add, export_format),
            file_name=f"new_numbers.{export_format}",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if export_format == 'xlsx' else "text/plain",
            button_key="download_new_button" # เพิ่ม key
        )
    if st.session_state.duplicates_found:
        download_button(
            label=f"ดาวน์โหลดเบอร์ที่ซ้ำ ({len(st.session_state.duplicates_found)} เบอร์)",
            data=create_export_file(st.session_state.duplicates_found, export_format),
            file_name=f"duplicate_numbers.{export_format}",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if export_format == 'xlsx' else "text/plain",
            button_key="download_duplicates_button" # เพิ่ม key
        )
    if st.session_state.combined_numbers:
        download_button(
            label=f"ดาวน์โหลดเบอร์ทั้งหมดในไฟล์รวมเบอร์ ({len(st.session_state.combined_numbers)} เบอร์)",
            data=create_export_file(st.session_state.combined_numbers, export_format),
            file_name=f"all_combined_numbers.{export_format}",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if export_format == 'xlsx' else "text/plain",
            button_key="download_all_combined_button" # เพิ่ม key
        )



### 3. ค้นหาเบอร์โทรศัพท์

search_number_input = st.text_input("ป้อนเบอร์โทรศัพท์ที่ต้องการค้นหา (เช่น 08XXXXXXXX)", key='search_number_input')

if st.button("ค้นหาเบอร์", key="search_button"): # เพิ่ม key
    if search_number_input:
        normalized_search_number = normalize_phone_number(search_number_input)
        if normalized_search_number:
            if normalized_search_number in st.session_state.combined_numbers:
                st.success(f"พบเบอร์ {hide_last_four_digits(normalized_search_number)} ในไฟล์รวมเบอร์แล้ว")
                update_status(f"ค้นหา: พบเบอร์ {hide_last_four_digits(normalized_search_number)}")
            else:
                st.warning(f"ไม่พบเบอร์ {hide_last_four_digits(normalized_search_number)} ในไฟล์รวมเบอร์")
                update_status(f"ค้นหา: ไม่พบเบอร์ {hide_last_four_digits(normalized_search_number)}")
        else:
            st.error("รูปแบบเบอร์โทรศัพท์ไม่ถูกต้อง โปรดป้อนเบอร์โทรศัพท์ 10 หลักที่ขึ้นต้นด้วย 0")
    else:
        st.warning("โปรดป้อนเบอร์โทรศัพท์ที่ต้องการค้นหา")



# การจัดการไฟล์ข้อมูล

clear_password = st.text_input("รหัสผ่านสำหรับล้างไฟล์รวมเบอร์", type="password", key='clear_password_input') # แก้ไข key ให้ไม่ซ้ำ

if st.button("ล้างไฟล์รวมเบอร์", key="clear_combined_button"): # เพิ่ม key
    if clear_password == "555+":
        st.warning("คุณแน่ใจหรือไม่ว่าต้องการลบเบอร์ทั้งหมดในไฟล์รวมเบอร์? การดำเนินการนี้ไม่สามารถย้อนกลับได้!")
        
        # เพิ่มปุ่มยืนยันอีกครั้งเพื่อความปลอดภัย
        if st.button("ยืนยันการลบ", key='confirm_clear_button'): # เพิ่ม key
            try:
                with open(COMBINED_NUMBERS_FILE, 'w', encoding='utf-8') as f:
                    f.write("")
                with open(UPLOADED_FILES_LOG, 'w', encoding='utf-8') as f:
                    f.write("")
                st.session_state.combined_numbers = set()
                st.success("ลบเบอร์ในไฟล์รวมเบอร์ทั้งหมดเรียบร้อยแล้ว")
                st.session_state.status_message.append("ไฟล์รวมเบอร์ถูกลบแล้ว")
                st.rerun()
            except Exception as e:
                st.error(f"ข้อผิดพลาดในการลบ: {e}")
    elif clear_password != "":
        st.error("รหัสผ่านไม่ถูกต้อง")