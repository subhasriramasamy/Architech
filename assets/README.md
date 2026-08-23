# assets/

Place an optional `logo.png` here if you want to replace the 🛡️ emoji icon
used in the app header/sidebar with a custom logo image. The app currently
renders its branding with CSS + emoji so it works out of the box with zero
image assets required.

To use a custom logo, add this near the top of `app.py`'s Home section:

```python
from PIL import Image
logo = Image.open("assets/logo.png")
st.image(logo, width=120)
```
