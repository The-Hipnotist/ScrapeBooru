import json, os, time, requests, shutil
from tkinter import (
    Tk,
    Label,
    Entry,
    Button,
    IntVar,
    Checkbutton,
    StringVar,
    messagebox as mb
)
def get_json(url, headers):
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def filter_images(data, max_resolution, include_posts_with_parent):
    supported_types = (".png", ".jpg", ".jpeg")
    posts = data.get("post", [])

    if not posts:
        mb.showinfo("Info", "No images found for the provided tags.")
        return []
    return [p["file_url"] if p["width"]*p["height"] <= max_resolution**2 else p["sample_url"] for p in posts if (p["parent_id"] == 0 or include_posts_with_parent) and p["file_url"].lower().endswith(supported_types)]

def download_image(url, folder):
    response = requests.get(url, stream=True)
    file_name = os.path.join(folder, url.split("/")[-1])
    with open(file_name, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)

def download_images():
    tags = tags_var.get().replace(" ", "+").replace("(", "%28").replace(")", "%29").replace(":", "%3a").replace("&", "%26")
    max_resolution = int(max_resolution_var.get())
    total_limit = int(total_limit_var.get())
    include_posts_with_parent = include_posts_with_parent_var.get()

    url = "https://gelbooru.com/index.php?page=dapi&json=1&s=post&q=index&limit=100&tags={}".format(tags)
    user_agent = "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +http://www.google.com/bot.html) Chrome/93.0.4577.83 Safari/537.36"
    headers = {"User-Agent": user_agent}

    try:
        data = get_json(url, headers)
        print("DEBUG: Data received:", data)
        count = int(data["@attributes"]["count"])

        if count == 0:
            mb.showinfo("Info", "No results found!")
            return
        
        image_urls = set()
        image_urls = image_urls.union(filter_images(data, max_resolution, include_posts_with_parent))

        for i in range(total_limit // 100):
            if count <= 0:
                break
            time.sleep(0.1)
            data = get_json(url + f"&pid={i+1}", headers)
            image_urls = image_urls.union(filter_images(data, max_resolution, include_posts_with_parent))

        images_folder = os.path.join(os.getcwd(), "downloaded_images")
        os.makedirs(images_folder, exist_ok=True)

        for img_url in image_urls:
            download_image(img_url, images_folder)

        mb.showinfo("Success", f"Downloaded {len(image_urls)} images!")
    except Exception as e:
        print(e)
        mb.showerror("Error", str(e))

root = Tk()
root.title("Scrapebooru")

Label(root, text="Tags:").grid(row=0, column=0, padx=10, pady=10)
tags_var = StringVar()
Entry(root, textvariable=tags_var).grid(row=0, column=1, padx=10, pady=10)

Label(root, text="Max Resolution:").grid(row=1, column=0, padx=10, pady=10)
max_resolution_var = StringVar(value="3072")
Entry(root, textvariable=max_resolution_var).grid(row=1, column=1, padx=10, pady=10)

Label(root, text="Total Limit:").grid(row=2, column=0, padx=10, pady=10)
total_limit_var = StringVar(value="100")
Entry(root, textvariable=total_limit_var).grid(row=2, column=1, padx=10, pady=10)

include_posts_with_parent_var = IntVar(value=1)
Checkbutton(root, text="Include posts with parent", variable=include_posts_with_parent_var).grid(row=3, columnspan=2, padx=10, pady=10)

Button(root, text="Download Images", command=download_images).grid(row=4, columnspan=2, padx=10, pady=10)

root.mainloop()