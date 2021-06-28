from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, EqualTo, Length, Regexp, Required
import re


class RegisterForm(FlaskForm):
    user_id = StringField(
        "아이디",
        validators=[
            DataRequired(message="아이디를 입력하세요."),
            Length(min=1, max=8, message="아이디는 8자리까지만 입력 가능합니다."),
            Regexp("^[A-Za-z][A-Za-z0-9]+$", message="아이디는 영문 대소문자와 숫자만 입력 가능합니다."),
        ],
    )
    user_email = StringField(
        "이메일",
        validators=[
            DataRequired(),
            Regexp(
                "[0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*@[0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*.[a-zA-Z]$"
            ),
        ],
    )
    user_name = StringField("이름", validators=[DataRequired(), Length(min=1, max=10)])
    user_password_confirm = PasswordField("비밀번호 확인", validators=[DataRequired()])
    user_password = PasswordField(
        "비밀번호",
        validators=[
            DataRequired(),
            Length(min=1, max=4),
            EqualTo("user_password_confirm"),
        ],
    )
    user_verification = StringField(
        "인증번호", validators=[DataRequired(message="인증번호를 입력하세요.")]
    )
