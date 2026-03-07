from PIL import Image

def process_image(input_path, output_path):
    img = Image.open(input_path).convert("RGBA")
    data = img.getdata()
    
    # Get the corner pixel to use as background color
    bg_color = data[0]
    print(f"Background color: {bg_color}")
    
    # Define a threshold for similarity
    threshold = 50
    
    def is_bg(pixel):
        return (abs(pixel[0] - bg_color[0]) < threshold and 
                abs(pixel[1] - bg_color[1]) < threshold and 
                abs(pixel[2] - bg_color[2]) < threshold)

    # Find bounding box
    width, height = img.size
    min_x = width
    min_y = height
    max_x = 0
    max_y = 0
    
    for y in range(height):
        for x in range(width):
            pixel = img.getpixel((x, y))
            if not is_bg(pixel):
                if x < min_x: min_x = x
                if x > max_x: max_x = x
                if y < min_y: min_y = y
                if y > max_y: max_y = y
                
    print(f"Bounding box: {min_x}, {min_y}, {max_x}, {max_y}")
    
    if min_x > max_x or min_y > max_y:
        print("Could not find logo")
        return
        
    # Add a small padding (e.g. 5% of width) but keep it square
    box_width = max_x - min_x
    box_height = max_y - min_y
    size = max(box_width, box_height)
    
    center_x = min_x + box_width // 2
    center_y = min_y + box_height // 2
    
    new_min_x = max(0, center_x - size // 2)
    new_max_x = min(width, center_x + size // 2)
    new_min_y = max(0, center_y - size // 2)
    new_max_y = min(height, center_y + size // 2)
    
    cropped = img.crop((new_min_x, new_min_y, new_max_x, new_max_y))
    
    # Make the background outside the circle transparent
    # The circle should essentially touch the borders of `cropped`
    # Let's create a circular mask
    mask = Image.new('L', cropped.size, 0)
    from PIL import ImageDraw
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, cropped.size[0], cropped.size[1]), fill=255)
    
    # Apply mask
    output = Image.new("RGBA", cropped.size)
    output.paste(cropped, (0, 0), mask)

    output.save(output_path)
    print(f"Saved cropped mask to {output_path}")

process_image("extension/images/icon-original.png", "extension/images/icon-cropped.png")
