from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import glob
import shutil
import sys

app = Flask(__name__, static_url_path='')

@app.route('/', methods=['GET', 'POST'])
def home():
    src_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    dst_dir = sys.argv[2] if len(sys.argv) > 2 else "keep"
    upscale_src_dir = sys.argv[3] if len(sys.argv) > 3 else None
    upscale_dst_dir = sys.argv[4] if len(sys.argv) > 4 else None
    print("SRC", src_dir)
    print("DST", dst_dir)

    if request.method == 'POST':
        img_name = request.form.get('fav_img')
        delete_img = request.form.get('delete_img')

        if img_name:
            print("KEEP")
            file_prefix = os.path.splitext(img_name)[0]

            for file_name in glob.glob(f"{src_dir}/{file_prefix}.*"):
                shutil.move(file_name, dst_dir)
                print("MV", file_name, dst_dir)
            if upscale_dst_dir is not None and upscale_dst_dir is not None:
                for file_name in glob.glob(f"{upscale_src_dir}/{file_prefix}.*"):
                    shutil.move(file_name, upscale_dst_dir)
                    print("MV", file_name, upscale_dst_dir)
        elif delete_img:
            print("DELETE")
            file_prefix = os.path.splitext(delete_img)[0]

            for file_name in glob.glob(f"{src_dir}/{file_prefix}.*"):
                os.remove(file_name)

        return redirect(url_for('home'))

    img_files = sorted([os.path.join('/', f) for f in os.listdir(src_dir) if f.endswith('.png')], key=lambda x: os.path.getmtime(src_dir + x))
    return render_template('index.html', img_files=img_files)

@app.route('/<path>.png')
def send_img(path):
    src_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    return send_from_directory(src_dir, path+".png")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8666, debug=True)

