import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from unidecode import unidecode
from youtubesearchpython.__future__ import VideosSearch
from AnonXMusic import app
from config import YOUTUBE_IMG_URL, BOT_USERNAME

def change_image_size(max_width, max_height, image):
    width_ratio = max_width / image.size[0]
    height_ratio = max_height / image.size[1]
    new_width = int(width_ratio * image.size[0])
    new_height = int(height_ratio * image.size[1])
    return image.resize((new_width, new_height))

def clear(text):
    words = text.split(" ")
    title = ""
    for word in words:
        if len(title) + len(word) < 60:
            title += " " + word
    return title.strip()

async def get_thumb(video_id, requester_pfp_url):
    cache_path = f"cache/{video_id}.png"
    if os.path.isfile(cache_path):
        return cache_path

    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        results = VideosSearch(url, limit=1)
        search_results = await results.next()
        result = search_results["result"][0]

        try:
            title = result["title"]
            title = re.sub(r"\W+", " ", title).title()
        except KeyError:
            title = "Unsupported Title"

        try:
            duration = result["duration"]
        except KeyError:
            duration = "Unknown Mins"

        thumbnail = result["thumbnails"][0]["url"].split("?")[0]

        try:
            views = result["viewCount"]["short"]
        except KeyError:
            views = "Unknown Views"

        try:
            channel = result["channel"]["name"]
        except KeyError:
            channel = "Unknown Channel"

        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    async with aiofiles.open(f"cache/thumb{video_id}.png", mode="wb") as f:
                        await f.write(await resp.read())

            async with session.get(requester_pfp_url) as resp:
                if resp.status == 200:
                    async with aiofiles.open(f"cache/requester_{video_id}.png", mode="wb") as f:
                        await f.write(await resp.read())

        youtube_image = Image.open(f"cache/thumb{video_id}.png")
        requester_image = Image.open(f"cache/requester_{video_id}.png").resize((100, 100), Image.ANTIALIAS).convert("RGBA")

        # Create circular mask for the requester profile picture
        mask = Image.new("L", (100, 100), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, 100, 100), fill=255)

        image1 = change_image_size(1280, 720, youtube_image)
        image2 = image1.convert("RGBA")
        background = image2.filter(ImageFilter.BoxBlur(5))  # Blurred background
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.7)  # Slightly enhance the brightness

        draw = ImageDraw.Draw(background)
        arial = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 30)
        font = ImageFont.truetype("AnonXMusic/assets/font.ttf", 30)

        # Calculate text width and position for BOT_USERNAME
        bot_username_text = unidecode(BOT_USERNAME)
        text_width, text_height = draw.textsize(bot_username_text, font=arial)
        position = (background.width - text_width - 20, 20)  # 20 pixels padding from right and top

        draw.text(position, bot_username_text, fill="white", font=arial)
        draw.text((55, 560), f"{channel} | {views[:23]}", fill="white", font=arial)
        draw.text((57, 600), clear(title), fill="white", font=font)
        draw.line([(55, 660), (1220, 660)], fill="white", width=5, joint="curve")
        draw.ellipse([(918, 648), (942, 672)], outline="white", fill="white", width=15)
        draw.text((36, 685), "00:00", fill="white", font=arial)
        draw.text((1185, 685), duration[:23], fill="white", font=arial)

        # Paste requester's profile picture on right middle side and left middle side
        background.paste(requester_image, (1080, 310), mask)
        background.paste(requester_image, (100, 310), mask)

        os.remove(f"cache/thumb{video_id}.png")
        os.remove(f"cache/requester_{video_id}.png")
        background.save(cache_path)
        return cache_path
    except TypeError as e:
        print(f"TypeError: {e}")
    except Exception as e:
        print(f"Exception: {e}")
    return YOUTUBE_IMG_URL

