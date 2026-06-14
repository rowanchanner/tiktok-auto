import os
import tiktokautouploader.function as tf
import patch_uploader
from playwright.sync_api import sync_playwright

patch_uploader.patch()

with sync_playwright() as p:
    tf.upload_tiktok(
        video="sample.mp4",
        description="Testing headless=False",
        accountname="rowanoutdoors",
        headless=False,
        cookies=r"C:\Users\churc\OneDrive\Desktop\nope\rowanoutdoors.txt"
    )
