from django import forms


class BaseForm(forms.Form):
    """Base form that adds DaisyUI error styling to fields with errors."""

    form_title = "Form"
    submit_text = "Submit"
    cancel_url = None

    def full_clean(self):
        super().full_clean()
        for field_name in self.errors:
            if field_name in self.fields:
                field = self.fields[field_name]
                current_class = field.widget.attrs.get("class", "")
                if "input-error" not in current_class:
                    field.widget.attrs["class"] = f"{current_class} input-error".strip()
