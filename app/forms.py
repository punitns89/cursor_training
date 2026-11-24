"""WTForms with CSRF (via Flask-WTF)."""

from flask_wtf import FlaskForm
from wtforms import IntegerField, PasswordField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=64)])
    password = PasswordField("Password", validators=[DataRequired(), Length(max=256)])
    submit = SubmitField("Sign in")


class ServerForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=128)])
    host = StringField("Hostname / IP", validators=[DataRequired(), Length(max=255)])
    port = IntegerField(
        "SSH port",
        default=22,
        validators=[DataRequired(), NumberRange(min=1, max=65535)],
    )
    ssh_username = StringField("SSH username", validators=[DataRequired(), Length(max=128)])
    ssh_password = PasswordField("SSH password", validators=[Optional(), Length(max=512)])
    ssh_private_key = TextAreaField(
        "SSH private key (PEM)", validators=[Optional(), Length(max=16384)]
    )
    tags = StringField("Tags / environment", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Save")

    def validate(self, extra_validators=None):
        ok = super().validate(extra_validators=extra_validators)
        if not ok:
            return False
        # On create, require at least one auth method. Edit may leave blank to keep existing.
        return True

    def require_auth_present(self, existing=None):
        """Ensure password or key is provided (or already stored on existing server)."""
        has_new = bool(self.ssh_password.data) or bool(
            self.ssh_private_key.data and self.ssh_private_key.data.strip()
        )
        has_existing = False
        if existing is not None:
            has_existing = existing.has_ssh_auth()
        if not has_new and not has_existing:
            raise ValidationError(
                "Provide an SSH password or a private key (PEM)."
            )
