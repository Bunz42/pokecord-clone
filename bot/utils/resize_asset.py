import os
from PIL import Image, ImageSequence

# -------------------------------------------------Asset Management----------------------------------------------------------- #
def scale_gif(input_path, output_path, scale_factor):
    """
    Scales a GIF upward while maintaining image quality and background transparency.
    
    :param input_path: Path to the original GIF.
    :param output_path: Path to save the scaled GIF.
    :param scale_factor: Multiplier for scaling (e.g., 2.0 to double the size).
    """
    with Image.open(input_path) as img:
        # Calculate new dimensions
        new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
        
        frames = []
        # Iterate through every frame in the GIF
        for frame in ImageSequence.Iterator(img):
            # 1. Convert to RGBA for smooth resizing
            rgba = frame.convert("RGBA")
            
            # 2. Resize using LANCZOS for the highest possible upscaling quality
            resized_rgba = rgba.resize(new_size, Image.Resampling.LANCZOS)
            
            # 3. Extract the alpha channel to determine which pixels should be transparent
            alpha = resized_rgba.split()[3]
            
            # Create a binary mask: pixels with alpha < 128 become fully transparent
            mask = Image.eval(alpha, lambda a: 255 if a < 128 else 0)
            
            # 4. Quantize the RGB image down to 255 colors (reserving 1 slot for transparency)
            rgb = resized_rgba.convert("RGB")
            quantized = rgb.quantize(colors=255, method=Image.Quantize.MAXCOVERAGE)
            
            # 5. Force the transparent pixels to use index 255
            quantized.paste(255, mask)
            
            frames.append(quantized)

        # 6. Save the newly compiled frames as an animated GIF
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=img.info.get('duration', 100), # Preserve original frame rate
            loop=img.info.get('loop', 0),           # Preserve original loop behavior
            disposal=2,                             # Disposal 2 prevents frames from smearing/overlapping
            transparency=255                        # Explicitly declare index 255 as the transparent color
        )
        
        print(f"Successfully scaled GIF saved to: {output_path}")
# ---------------------------------------------------------------------------------------------------------------------------- #

input_gif = "assets/showdown/25.gif"
output_gif = "assets/scaled_sprites/regular/pikachu.gif"

scale_gif(
    input_path=input_gif, 
    output_path=output_gif,
    scale_factor=5.0
)