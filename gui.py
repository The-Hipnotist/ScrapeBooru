import json, os, time, requests, shutil
from tkinter import (
    Tk,
    ttk,
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

def download_image(url, folder, max_retries):
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, stream=True)
            file_name = os.path.join(folder, url.split("/")[-1])
            with open(file_name, 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
            return True
        except Exception as e:
            if attempt == max_retries:
                if not suppress_errors_var.get():
                    mb.showerror("Error", f"Failed to download {url}: {str(e)}")
                return False
            time.sleep(1)

def update_progress_bar(progress_bar, progress, total):
    progress_bar["value"] = (progress / total) * 100
    root.update_idletasks()

def download_images():
    tags = tags_var.get().replace(" ", "+").replace("(", "%28").replace(")", "%29").replace(":", "%3a").replace("&", "%26")
    max_resolution = int(max_resolution_var.get())
    total_limit = int(total_limit_var.get())
    include_posts_with_parent = include_posts_with_parent_var.get()

    url = "https://gelbooru.com/index.php?page=dapi&json=1&s=post&q=index&limit=100&tags={}".format(tags)
    user_agent = "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +http://www.google.com/bot.html) Chrome/93.0.4577.83 Safari/537.36"
    headers = {"User-Agent": user_agent}

    max_retries = int(retries_var.get()) if retry_download_var.get() else 0

    try:
        data = get_json(url, headers)
        if show_debug_messages_var.get():
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

        progress_bar["maximum"] = len(image_urls)
        for idx, img_url in enumerate(image_urls):
            download_image(img_url, images_folder, max_retries)
            update_progress_bar(progress_bar, idx + 1, len(image_urls))

        progress_bar["value"] = 0
        root.update_idletasks()

        mb.showinfo("Success", f"Downloaded {len(image_urls)} images!")
    except Exception as e:
        if not suppress_errors_var.get():
            mb.showerror("Error", str(e))

def toggle_advanced_options():
    if advaned_options_var.get():
        show_debug_messages_cb.grid(row=7, columnspan=2, padx=10, pady=2)
        retry_download_cb.grid(row=8, columnspan=2, padx=10, pady=2)
        retries_label.grid(row=9, column=0, padx=10, pady=2)
        retries_entry.grid(row=9, column=1, padx=10, pady=2)
        suppress_errors_cb.grid(row=10, columnspan=2, padx=10, pady=2)
    else:
        show_debug_messages_cb.grid_remove()
        retry_download_cb.grid_remove()
        retries_label.grid_remove()
        retries_entry.grid_remove()
        suppress_errors_cb.grid_remove()

root = Tk()
root.title("Scrapebooru")
root.resizable(False, False)

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

progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
progress_bar.grid(row=5, columnspan=2, padx=10, pady=10)

advaned_options_var = IntVar()
Checkbutton(root, text="Show Advanced Options", variable=advaned_options_var, command=toggle_advanced_options).grid(row=6, columnspan=2, padx=10, pady=0)

show_debug_messages_var = IntVar()
show_debug_messages_cb = Checkbutton(root, text="Show debug messages in console", variable=show_debug_messages_var)
retry_download_var = IntVar()
retry_download_cb = Checkbutton(root, text="Retry download if failed.", variable=retry_download_var, command=lambda: retries_entry.config(state="normal" if retry_download_var.get() else "disabled"))
retries_var = StringVar(value="1")
retries_label = Label(root, text="Max Retries:")
retries_entry = Entry(root, textvariable=retries_var, state="disabled")
suppress_errors_var = IntVar()
suppress_errors_cb = Checkbutton(root, text="Attempt to suppress errors?", variable=suppress_errors_var)
root.mainloop()
