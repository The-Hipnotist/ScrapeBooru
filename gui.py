import json, os, time, requests, shutil, requests, threading, itertools, sys
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
from tkinter import ttk

def get_json(url, headers):
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def filter_images(data, max_resolution, include_posts_with_parent):
    supported_types = (".png", ".jpg", ".jpeg")
    posts = data.get("post", [])

    if not posts:
        pass
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

def download_images_thread():
    tags = tags_var.get().replace(" ", "+").replace("(", "%28").replace(")", "%29").replace(":", "%3a").replace("&", "%26")
    max_resolution = int(max_resolution_var.get())
    total_limit = int(total_limit_var.get())
    include_posts_with_parent = include_posts_with_parent_var.get()
    accurate_total_limit = accurate_total_limit_var.get()


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

        mb.showinfo("Success", f"Downloaded {len(image_urls)} images!")
    except Exception as e:
        if not suppress_errors_var.get():
            mb.showerror("Error", str(e))

def download_images():
    threading.Thread(target=download_images_thread).start()

def toggle_advanced_options():
    if advanced_options_var.get():
        advanced_frame.grid(row=8, columnspan=2, padx=10, pady=5, sticky="ew")
    else:
        advanced_frame.grid_remove()

def toggle_deprecated_options():
    if deprecated_options_var.get():
        suppress_errors_cb.grid(row=6, columnspan=2, padx=10, pady=2)
    else:
        suppress_errors_cb.grid_remove()

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
    Version 1.2.0:
    - Improved UI.
    - Fixed bug that would cause tkinter to not respond while downloading the images.
    
    Version 1.3.0:
    - Fixed bug that would pop up a window saying 'No posts found with tag', but then would download the image anyway.
    
    Version 1.3.5:
    - Added "Suppress errors" to deprecated options.

    Version 1.4.0:
    - Added new advanced options.
    """
    changelog_text.insert("1.0", changelog_content)
    changelog_text.config(state='disabled')

root = Tk()
root.title("Scrapebooru")
root.resizable(False, False)

main_frame = ttk.Frame(root)
main_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

Label(main_frame, text="Tags:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
tags_var = StringVar()
Entry(main_frame, textvariable=tags_var).grid(row=0, column=1, padx=10, pady=5)

Label(main_frame, text="Max Resolution:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
max_resolution_var = StringVar(value="3072")
Entry(main_frame, textvariable=max_resolution_var).grid(row=1, column=1, padx=10, pady=5)

Label(main_frame, text="Total Limit:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
total_limit_var = StringVar(value="100")
Entry(main_frame, textvariable=total_limit_var).grid(row=2, column=1, padx=10, pady=5)

include_posts_with_parent_var = IntVar(value=1)
Checkbutton(main_frame, text="Include posts with parent", variable=include_posts_with_parent_var).grid(row=3, columnspan=2, padx=10, pady=5)

Button(main_frame, text="Download Images", command=download_images).grid(row=4, column=0, padx=10, pady=10)
Button(main_frame, text="Changelog", command=show_changelog).grid(row=4, column=1, padx=10, pady=10, sticky="w")

progress_bar = ttk.Progressbar(main_frame, orient="horizontal", length=350, mode="determinate")
progress_bar.grid(row=5, columnspan=2, padx=10, pady=5)

advanced_options_var = IntVar()
Checkbutton(main_frame, text="Show advanced options", variable=advanced_options_var, command=toggle_advanced_options).grid(row=6, columnspan=2, padx=10, pady=10)

advanced_frame = ttk.Frame(root)
show_debug_messages_var = IntVar()
Checkbutton(advanced_frame, text="Show debug messages in console", variable=show_debug_messages_var).grid(row=0, columnspan=2, padx=10, pady=2)

retry_download_var = IntVar()
Checkbutton(advanced_frame, text="Retry download if failed", variable=retry_download_var, command=lambda: retries_entry.config(state="normal" if retry_download_var.get() else "disabled")).grid(row=1, columnspan=2, padx=10, pady=2)

retries_var = StringVar(value="1")
Label(advanced_frame, text="Max Retries:").grid(row=2, column=0, padx=10, pady=2, sticky="e")
retries_entry = Entry(advanced_frame, textvariable=retries_var, state="disabled")
retries_entry.grid(row=2, column=1, padx=10, pady=2, sticky="w")

accurate_progress_bar_var = IntVar()
Checkbutton(advanced_frame, text="Make progress bar more accurate (EXPERIMENTAL)", variable=accurate_progress_bar_var).grid(row=3, columnspan=2, padx=10, pady=2)

accurate_total_limit_var = IntVar()
Checkbutton(advanced_frame, text="Ensure total limit is accurate", variable=accurate_total_limit_var).grid(row=4, columnspan=2, padx=10, pady=2)

deprecated_options_var = IntVar()
Checkbutton(advanced_frame, text="Show deprecated options", variable=deprecated_options_var, command=toggle_deprecated_options).grid(row=5, columnspan=2, padx=10, pady=2)


suppress_errors_var = IntVar()
suppress_errors_cb = Checkbutton(advanced_frame, text="Attempt to suppress errors (DEPRECATED)", variable=suppress_errors_var)
suppress_errors_cb.grid_remove()

root.mainloop()
