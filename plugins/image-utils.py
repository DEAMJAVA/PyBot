from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests
from io import BytesIO
import discord

from main import bot, add_help, get_average_color, logerr


@bot.command()
async def addcaption(ctx, url, *, args):
    try:
        response = requests.get(url)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))

        draw = ImageDraw.Draw(image)

        font_name = "arial.ttf"
        font_size = 20
        text_color = "white"
        position = (10, 10)

        params = args.split("-")
        text = params[0].strip()
        for param in params[1:]:
            key, value = param.split("=")
            if key.strip() == "font":
                font_name = value.strip()
            elif key.strip() == "size":
                font_size = int(value.strip())
            elif key.strip() == "color":
                text_color = value.strip()
            elif key.strip() == "pos":
                position = tuple(map(int, value.strip().split(",")))

        for guild_emoji in ctx.guild.emojis:
            emoji_str = f":{guild_emoji.name}:"
            if emoji_str in text:
                emoji_url = guild_emoji.url
                response = requests.get(emoji_url)
                emoji_image = Image.open(BytesIO(response.content))
                emoji_image = emoji_image.resize((font_size, font_size), Image.ANTIALIAS)
                image.paste(emoji_image, position, emoji_image)
                text = text.replace(emoji_str, "")

        # Render the remaining text using a regular font
        font = ImageFont.truetype(font_name, font_size)
        draw.text(position, text, fill=text_color, font=font)

        image.save("captioned_image.png")
        await ctx.send(file=discord.File("captioned_image.png"))
    except requests.HTTPError as e:
        await ctx.send(f"HTTP Error: {e}")
    except Exception as e:
        await ctx.send(f"Error: {e}")
add_help('Image Utils', 'addcaption <image link> <text> <-font=/size=/color=/pos=pos,pos>', 'Adds caption to an image')

def adjust_filter_strength(image, filter_name, percentage):
    if percentage == 100:
        return image.filter(filter_name)
    elif percentage == 0:
        return image
    else:
        return image.filter(filter_name).filter(ImageFilter.ModeFilter(size=int(percentage * 0.1)))

@bot.command()
async def applyfilter(ctx, url, filter_name, percentage=100):
    try:
        percentage = max(0, min(100, int(percentage)))
        response = requests.get(url)
        response.raise_for_status()  # Check if URL is valid
        image = Image.open(BytesIO(response.content))

        # Convert the image to RGB mode if it's in palette mode
        if image.mode == "P":
            image = image.convert("RGB")

        if filter_name == "grayscale":
            image = image.convert('L')
        elif filter_name == "blur":
            image = adjust_filter_strength(image, ImageFilter.BLUR, percentage)
        elif filter_name == "sharpen":
            image = adjust_filter_strength(image, ImageFilter.SHARPEN, percentage)
        elif filter_name == "contour":
            image = adjust_filter_strength(image, ImageFilter.CONTOUR, percentage)
        elif filter_name == "edgeenhance":
            image = adjust_filter_strength(image, ImageFilter.EDGE_ENHANCE, percentage)
        elif filter_name == "emboss":
            image = adjust_filter_strength(image, ImageFilter.EMBOSS, percentage)
        elif filter_name == "detail":
            image = adjust_filter_strength(image, ImageFilter.DETAIL, percentage)
        elif filter_name == "smooth":
            image = adjust_filter_strength(image, ImageFilter.SMOOTH, percentage)
        elif filter_name == "find_edges":
            image = adjust_filter_strength(image, ImageFilter.FIND_EDGES, percentage)
        elif filter_name == "gaussian_blur":
            image = adjust_filter_strength(image, ImageFilter.GaussianBlur(radius=percentage/100 * 2), percentage)
        elif filter_name == "unsharp_mask":
            image = adjust_filter_strength(image, ImageFilter.UnsharpMask(radius=percentage/100 * 2, percent=150), percentage)
        else:
            await ctx.send("Invalid filter name. Available filters: grayscale, blur, sharpen, contour, edgeenhance, emboss, detail, smooth, find_edges, gaussian_blur, unsharp_mask")
            return

        image.save("filtered_image.png")
        await ctx.send(file=discord.File("filtered_image.png"))
    except requests.HTTPError as e:
        await ctx.send(f"HTTP Error: {e}")
    except Exception as e:
        await ctx.send(f"Error: {e}")
add_help('Image Utils', 'applyfilter <image link> <blur/sharpen/contour/edgeenhance/emboss/detail/smooth/find_edges/gaissian_blur/unsharp_mask> [percentage]', 'applies filter to image')

@bot.command()
async def resizeimage(ctx, url, width=None, height=None):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check if URL is valid
        image = Image.open(BytesIO(response.content))

        # Resize the image if width and/or height are specified
        if width and height:
            image = image.resize((int(width), int(height)), Image.LANCZOS)
        elif width:
            ratio = float(width) / image.width
            height = int(image.height * ratio)
            image = image.resize((int(width), height), Image.LANCZOS)
        elif height:
            ratio = float(height) / image.height
            width = int(image.width * ratio)
            image = image.resize((width, int(height)), Image.LANCZOS)

        image.save("resized_image.png")
        await ctx.send(file=discord.File("resized_image.png"))
    except requests.HTTPError as e:
        await ctx.send(f"HTTP Error: {e}")
    except Exception as e:
        await ctx.send(f"Error: {e}")
add_help('Image Utils', 'resizeimage <image link> <width> <height>', 'Resizes a given image')


@bot.command()
async def rotateimage(ctx, url, angle=90):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check if URL is valid
        image = Image.open(BytesIO(response.content))

        # Rotate the image by the specified angle
        rotated_image = image.rotate(int(angle), expand=True)

        rotated_image.save("rotated_image.png")
        await ctx.send(file=discord.File("rotated_image.png"))
    except requests.HTTPError as e:
        await ctx.send(f"HTTP Error: {e}")
    except Exception as e:
        await ctx.send(f"Error: {e}")
add_help('Image Utils', 'rotateimage <image link [angle]', 'Rotates an image by a given angle else by 90 degree')

@bot.command()
async def cropimage(ctx, url, x1, y1, x2, y2):
    try:
        response = requests.get(url)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))

        cropped_image = image.crop((int(x1), int(y1), int(x2), int(y2)))

        cropped_image.save("cropped_image.png")
        await ctx.send(file=discord.File("cropped_image.png"))
    except requests.HTTPError as e:
        await ctx.send(f"HTTP Error: {e}")
    except Exception as e:
        await ctx.send(f"Error: {e}")
add_help('Image Utils', 'cropimage <image link <pos 1> <pos 2> <pos 3> <pos 4>', 'Crops an image by the given points')


@bot.command()
async def avgcolor(ctx, url=None):
    if url:
        try:
            color = await get_average_color(url)
            rgb_to_hex = lambda r, g, b: f'#{r:02x}{g:02x}{b:02x}'
            hex_color = rgb_to_hex(color[0], color[1], color[2])
            await ctx.send(f'The average color of your image is: {hex_color}, R: {color[0]}, G: {color[1]}, B: {color[2]}')
        except requests.HTTPError as e:
            await ctx.send(f"HTTP Error: {e}")
        except Exception as e:
            logerr(f"Error: {e}")
    else:
        await ctx.send('Please provide an image url')
add_help('Image Utils', 'avgcolor <image link>', 'Returns the most average color of the image')
