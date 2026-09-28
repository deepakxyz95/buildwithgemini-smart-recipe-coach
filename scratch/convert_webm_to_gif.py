import imageio
from PIL import Image

input_path = "/config/.gemini/antigravity/brain/9a29300b-6a03-4b81-9593-3bb11bbd7c36/scratch/agent_demo.webm"
output_path = "/config/Desktop/Session1/smart-recipe-coach/demo.gif"

print(f"Reading {input_path}...")
reader = imageio.get_reader(input_path)
fps = reader.get_meta_data().get('fps', 25)
print(f"Original FPS: {fps}")

frames = []
step = 2  # sample every 2nd frame to optimize size (~12 fps)
for i, frame in enumerate(reader):
    if i % step == 0:
        img = Image.fromarray(frame)
        # Resize to max 800 width while preserving aspect ratio
        w, h = img.size
        if w > 800:
            new_w = 800
            new_h = int(h * (800 / w))
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        # Quantize colors to 128 colors for optimal GIF size
        img_quantized = img.quantize(colors=128)
        frames.append(img_quantized)

print(f"Extracted {len(frames)} frames. Saving looping GIF to {output_path}...")
frames[0].save(
    output_path,
    save_all=True,
    append_images=frames[1:],
    optimize=True,
    duration=int(1000 / (fps / step)),
    loop=0
)
print("Conversion complete!")
