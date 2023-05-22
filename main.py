import json
import streamlit as st
from streamlit_autorefresh import st_autorefresh

import decrypt
import totp

st.set_page_config(
    page_title="猫猫的在线 Aegis 备份查看器",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.header("🐾 Foges，猫猫的在线 Aegis 备份查看器 🐾")
st.markdown(
    unsafe_allow_html=True,
    body="""

*目前只支持标准 TOTP，HOTP 和其它格式不保证完全支援。*
""",
)

with st.sidebar:
    with st.form("选择文件"):
        uploaded_file = st.file_uploader("上传你的 Aegis 备份", type="json")
        is_encrypted_checkbox = st.checkbox("你的 Aegis 备份是否加密", value=False)
        is_show_secret_checkbox = st.checkbox("是否要显示密钥", value=False)

        period_time = st.number_input(
            "几秒后刷新一次页面", step=1, value=10, min_value=1, max_value=60
        )
        st.form_submit_button("确认按钮")

        if uploaded_file == None:
            st.warning("未选择文件")

    with st.form("输入密码"):
        password_text_input = st.text_input(
            "在这里输入加密密码", type="password", disabled=not is_encrypted_checkbox
        )
        st.form_submit_button(
            "确认密码",
            disabled=is_encrypted_checkbox == False
            or (is_encrypted_checkbox == True and password_text_input == None),
        )
    st_autorefresh(interval=period_time * 1000)

    def decrypt_items():
        if is_encrypted_checkbox == True:
            try:
                entries_list = json.loads(
                    decrypt.decrypt(
                        uploaded_file.read().decode("utf-8"), password_text_input
                    )
                )["entries"]
                # st.write(entries_list)
                return entries_list
            except:
                st.error("出错了！这看起来是你的错误，试试修改解密选项。")
        elif is_encrypted_checkbox == False:
            try:
                entries_list = json.loads(uploaded_file.read().decode("utf-8"))["db"][
                    "entries"
                ]
                # st.write(entries_list)
                return entries_list
            except:
                st.error("出错了！这看起来是你的错误，试试修改解密选项。")


def show_2fa_table(entries_list):
    table_content = ""
    table_begin = """<style>table{border-collapse:collapse;white-space:nowrap;}td,th{border:1pxsolidblack;padding:5px;}</style><table><tr><td>图标</td><td>网站</td><td>用户名</td><td>验证码</td><td>类型</td><td>加密算法</td><td>数字数</td><td>周期/计数</td><td>密钥</td></tr>"""
    for item in entries_list:
        if item["type"] == "totp":
            type = "TOTP"
            number = totp.totp(
                key=item["info"]["secret"],
                time_step=item["info"]["period"],
                digits=item["info"]["digits"],
                digest=item["info"]["algo"],
            )
            counter_or_period_info = item["info"]["period"]

        elif item["type"] == "hotp":
            type = "HOTP"
            number = totp.hotp(
                key=item["info"]["secret"],
                counter=item["info"]["counter"],
                digits=item["info"]["digits"],
                digest=item["info"]["algo"],
            )

            counter_or_period_info = item["info"]["counter"]

        else:
            type = item["type"] if item["type"] else "错误的类型"
            number = "不支持的类型"

        if item["icon"] != None:
            base64_icon = item["icon"]
        else:
            with open("assets/default_icon.svg") as f:
                base64_icon = f.read()

        secret = item["info"]["secret"] if is_show_secret_checkbox else 114514

        table_content = (
            table_content
            + f"""<tr><td><img src="data:image/svg+xml;base64,{base64_icon}" width="100%" height="100%"></td><td>{item["issuer"]}</td><td>{item["name"]}</td><td><b>{number}</b></td><td>{type}</td><td>{item["info"]["algo"]}</td><td>{item["info"]["digits"]}</td><td>{counter_or_period_info}</td><td>{secret}</td></tr>"""
        )

    table = table_begin + table_content
    st.markdown(table, unsafe_allow_html=True)


if not uploaded_file:
    with open("assets/sample.json") as uploaded_file:
        entries_list = json.load(uploaded_file)["db"]["entries"]
        show_2fa_table(entries_list)
else:
    show_2fa_table(decrypt_items())
