import base64
png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
with open("public/assets/profile_pics/default.png", "wb") as f:
    f.write(base64.b64decode(png_b64))
print("Created default.png")
