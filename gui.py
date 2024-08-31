import json, os, time, requests, shutil, threading
from tkinter import (
    Tk,
    Label,
    Entry,
    Button,
    IntVar,
    Checkbutton,
    StringVar,
    messagebox as mb,
    Toplevel,
    Text,
    Scrollbar
)
import tkinter as tk
from tkinter import ttk

def get_json(url, headers):
    """
     Get JSON from a URL. This is a convenience function for making a GET request to a URL and checking the status code is returned
     
     @param url - The URL to make the request to
     @param headers - A dictionary of headers to send with the request
     
     @return The JSON returned from the request as a dictionary Raises requests. HTTPError if the status code is
    """
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def filter_images(data, max_resolution, include_posts_with_parent):
    supported_types = (".png", ".jpg", ".jpeg")
    posts = data.get("post", [])
    if not posts:
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
                mb.showerror("Error", f"Failed to download {url}: {str(e)}")
                return False
            time.sleep(1)

def update_progress_bar(progress_bar, progress, total):
    progress_bar["value"] = (progress / total) * 100
    root.update_idletasks()

def download_images():
    tags = tags_var.get().strip()
    if not tags:
        mb.showerror("Error", "Tags field cannot be empty!")
        return
    
    total_limit = int(total_limit_var.get())
    if total_limit == 0:
        download_all = mb.askokcancel("Downloading all images", "You have entered 0 as the total limit. This will proceed to download ALL the images under the supplied tag. If this was a mistake, press cancel. Otherwise, press OK.")
        if not download_all:
            return
        total_limit = 999

    status_var.set(f"Downloading {total_limit} images using tags: {tags}")
    
    threading.Thread(target=download_images_thread).start()

def download_images_thread():
    try:
        tags = tags_var.get().strip()
        if not tags:
            mb.showerror("Error", "Tags field cannot be empty!")
            return
        tags = tags_var.get().replace(" ", "+").replace("(", "%28").replace(")", "%29").replace(":", "%3a").replace("&", "%26")
        max_resolution = int(max_resolution_var.get())
        total_limit = int(total_limit_var.get())
        if total_limit == 0:
            download_all = mb.askokcancel("Downloading all images", "You have entered 0 as the total limit. This will proceed to download ALL the images under the supplied tag. If this was a mistake, press cancel. Otherwise, press OK.")
            if download_all == False:
                return
            else:
                total_limit = 999
        include_posts_with_parent = include_posts_with_parent_var.get()
        accurate_total_limit = accurate_total_limit_var.get()
        url = "https://gelbooru.com/index.php?page=dapi&json=1&s=post&q=index&limit=100&tags={}".format(tags)
        user_agent = "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +http://www.google.com/bot.html) Chrome/93.0.4577.83 Safari/537.36"
        headers = {"User-Agent": user_agent}

        max_retries = int(retries_var.get()) if retry_download_var.get() else 0

        data = get_json(url, headers)
        if show_debug_messages_var.get():
            print("DEBUG: Data received:", data)
        count = int(data["@attributes"]["count"])

        if count == 0:
            mb.showinfo("Info", "No results found!")
            return
        
        image_urls = set()
        image_urls = image_urls.union(filter_images(data, max_resolution, include_posts_with_parent))

        total_images = len(image_urls)
        for i in range(total_limit // 100):
            if count <= 0:
                break
            time.sleep(0.1)
            data = get_json(url + f"&pid={i+1}", headers)
            new_images = filter_images(data, max_resolution, include_posts_with_parent)
            image_urls = image_urls.union(new_images)
            if accurate_total_limit and total_images >= total_limit:
                break
        
        image_urls = list(image_urls)[:total_limit] if accurate_total_limit else image_urls

        images_folder = os.path.join(os.getcwd(), "downloaded_images")
        os.makedirs(images_folder, exist_ok=True)

        total_to_download = len(image_urls)
        progress_bar["maximum"] = total_to_download
        for idx, img_url in enumerate(image_urls):
            if download_image(img_url, images_folder, max_retries):
                update_progress_bar(progress_bar, idx + 1, total_to_download)

        progress_bar["value"] = 0
        root.update_idletasks()

        root.after(0, lambda: status_var.set(""))

        mb.showinfo("Success", f"Downloaded {len(image_urls)} images!")
    except Exception as e:
        root.after(0, lambda: status_var.set(""))
        mb.showerror("Error", str(e))

def show_changelog():
    changelog_window = Toplevel(root)
    changelog_window.title("Changelog")
    changelog_window.geometry("512x512")

    changelog_text = Text(changelog_window, wrap='word')
    changelog_text.pack(expand=True, fill='both')

    changelog_scrollbar = Scrollbar(changelog_text)
    changelog_scrollbar.pack(side='right', fill='y')
    changelog_text.config(yscrollcommand=changelog_scrollbar.set)
    changelog_scrollbar.config(command=changelog_text.yview)

    changelog_content = """
    Version 2.0
    - New UI changes. (If you want to use the old UI, please use the 1.0 branch on this repo.)
    - Added script merge warning to the accurate total limit option.
    """
    changelog_text.insert("2.0", changelog_content)
    changelog_text.config(state='disabled')

def show_accurate_limit_warning():
    if accurate_total_limit_var.get():
        mb.showwarning("Script merge warning", "This option will be merged with the main script by default in a new version.")

def create_ui():
    root = Tk()
    root.title("Scrapebooru")
    root.geometry("320x375")
    root.resizable(False, False)

    style = ttk.Style()
    style.theme_use('clam')

    main_frame = ttk.Frame(root, padding="10 10 10 10")
    main_frame.grid(row=0, column=0, sticky=(tk.N, tk.W, tk.E, tk.S))
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    input_frame = ttk.LabelFrame(main_frame, text="Search Settings", padding="5 5 5 5")
    input_frame.grid(row=0, column=0, sticky=(tk.N, tk.W, tk.E, tk.S), pady=(0, 5))
    input_frame.columnconfigure(1, weight=1)

    ttk.Label(input_frame, text="Tags:").grid(row=0, column=0, sticky=tk.W, pady=2)
    tags_var = StringVar()
    ttk.Entry(input_frame, textvariable=tags_var).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)

    ttk.Label(input_frame, text="Max Resolution:").grid(row=1, column=0, sticky=tk.W, pady=2)
    max_resolution_var = StringVar(value="3072")
    ttk.Entry(input_frame, textvariable=max_resolution_var).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)

    ttk.Label(input_frame, text="Total Limit:").grid(row=2, column=0, sticky=tk.W, pady=2)
    total_limit_var = StringVar(value="100")
    ttk.Entry(input_frame, textvariable=total_limit_var).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)
    ttk.Label(input_frame, text="(enter 0 for max)").grid(row=3, column=1, sticky=tk.W)

    options_frame = ttk.LabelFrame(main_frame, text="Options", padding="5 5 5 5")
    options_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))

    include_posts_with_parent_var = IntVar(value=1)
    ttk.Checkbutton(options_frame, text="Include posts with parent", variable=include_posts_with_parent_var).grid(row=0, column=0, sticky=tk.W, pady=1)

    show_debug_messages_var = IntVar()
    ttk.Checkbutton(options_frame, text="Show debug messages in console", variable=show_debug_messages_var).grid(row=1, column=0, sticky=tk.W, pady=1)

    retry_download_var = IntVar()
    ttk.Checkbutton(options_frame, text="Retry download if failed", variable=retry_download_var, command=lambda: retries_entry.config(state="normal" if retry_download_var.get() else "disabled")).grid(row=2, column=0, sticky=tk.W, pady=1)

    retries_frame = ttk.Frame(options_frame)
    retries_frame.grid(row=3, column=0, sticky=tk.W, pady=1)
    ttk.Label(retries_frame, text="Max Retries:").grid(row=0, column=0, sticky=tk.W)
    retries_var = StringVar(value="1")
    retries_entry = ttk.Entry(retries_frame, textvariable=retries_var, width=5, state="disabled")
    retries_entry.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))

    accurate_total_limit_var = IntVar()
    ttk.Checkbutton(options_frame, text="Ensure total limit is accurate", variable=accurate_total_limit_var, command=show_accurate_limit_warning).grid(row=4, column=0, sticky=tk.W, pady=1)

    buttons_frame = ttk.Frame(main_frame)
    buttons_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
    buttons_frame.columnconfigure(0, weight=1)
    buttons_frame.columnconfigure(1, weight=1)

    ttk.Button(buttons_frame, text="Download Images", command=download_images).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 2))
    ttk.Button(buttons_frame, text="Changelog", command=show_changelog).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(2, 0))

    progress_bar = ttk.Progressbar(main_frame, orient="horizontal", length=300, mode="determinate")
    progress_bar.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 5))

    status_var = StringVar()
    status_label = ttk.Label(main_frame, textvariable=status_var)
    status_label.grid(row=4, column=0, sticky=(tk.W, tk.E))

    return root, progress_bar, tags_var, max_resolution_var, total_limit_var, include_posts_with_parent_var, show_debug_messages_var, retry_download_var, retries_var, accurate_total_limit_var, status_var

root, progress_bar, tags_var, max_resolution_var, total_limit_var, include_posts_with_parent_var, show_debug_messages_var, retry_download_var, retries_var, accurate_total_limit_var, status_var = create_ui()

root.mainloop()
