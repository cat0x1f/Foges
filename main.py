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
        备份文件 = st.file_uploader("上传你的 Aegis 备份", type="json")
        是否加密 = st.checkbox("你的 Aegis 备份是否加密", value=False)
        是否显示密钥 = st.checkbox("是否要显示密钥", value=False)

        每次刷新时间 = st.number_input(
            "几秒后刷新一次页面", step=1, value=10, min_value=1, max_value=60
        )
        确认按钮 = st.form_submit_button("确认按钮")

        if 备份文件 == None:
            st.warning("未选择文件")

    with st.form("输入密码"):
        输入密码框 = st.text_input("在这里输入加密密码", type="password", disabled=not 是否加密)
        确认密码 = st.form_submit_button(
            "确认密码", disabled=是否加密 == False or (是否加密 == True and 输入密码框 == None)
        )
    st_autorefresh(interval=每次刷新时间 * 1000)

    # def 是否加密():
    #     if 备份文件:
    #         return True if json.loads(备份文件.read().decode("utf-8"))["headers"]["slots"] else False

    def 解密项目():
        if 是否加密 == True:
            try:
                解密后项目列表 = json.loads(
                    decrypt.decrypt(备份文件.read().decode("utf-8"), 输入密码框)
                )["entries"]
                # st.write(解密后项目列表)
                return 解密后项目列表
            except:
                st.error("有错误")
        if 是否加密 == False:
            try:
                解密后项目列表 = json.loads(备份文件.read().decode("utf-8"))["db"]["entries"]
                # st.write(解密后项目列表)
                return 解密后项目列表
            except:
                st.error("有错误")


def 显示两步验证(解密后项目列表):
    table_content = ""
    table_begin = """<table><tr><td>图标</td><td>网站</td><td>用户名</td><td>验证码</td><td>类型</td><td>加密算法</td><td>数字数</td><td>周期或计数</td><td>密钥</td></tr>"""
    for item in 解密后项目列表:
        if item["type"] == "totp":
            type = "TOTP"
            number = totp.totp(
                key=item["info"]["secret"],
                time_step=item["info"]["period"],
                digits=item["info"]["digits"],
                digest=item["info"]["algo"],
            )
            周期或计数 = item["info"]["period"]

        elif item["type"] == "hotp":
            type = "HOTP"
            number = totp.hotp(
                key=item["info"]["secret"],
                counter=item["info"]["counter"],
                digits=item["info"]["digits"],
                digest=item["info"]["algo"],
            )

            周期或计数 = item["info"]["counter"]

        else:
            number = "不支持的类型"

        if item["icon"] != None:
            base64_icon = item["icon"]
        else:
            with open("assets/default_icon.svg") as f:
                base64_icon = f.read()

        密钥 = item["info"]["secret"] if 是否显示密钥 else 114514

        table_content = (
            table_content
            + f"""<tr><td><img src="data:image/svg+xml;base64,{base64_icon}" width="100%" height="100%"></td><td>{item["issuer"]}</td><td>{item["name"]}</td><td><b>{number}</b></td><td>{type}</td><td>{item["info"]["algo"]}</td><td>{item["info"]["digits"]}</td><td>{周期或计数}</td><td>{密钥}</td></tr>"""
        )

    table = table_begin + table_content
    st.markdown(table, unsafe_allow_html=True)


if not 备份文件:
    with open("assets/aegis_plain.json") as 备份文件:
        解密后项目列表 = json.load(备份文件)["db"]["entries"]
        显示两步验证(解密后项目列表)
else:
    显示两步验证(解密项目())
