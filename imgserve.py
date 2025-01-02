from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import glob
import shutil
import sys

app = Flask(__name__, static_url_path='/assets', static_folder="assets")

@app.route('/', methods=['GET', 'POST'])
def home():
    src_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    dst_dir = sys.argv[2] if len(sys.argv) > 2 else "keep"
    
    print("CWD",os.getcwd())
    print("SRC", src_dir)
    print("DST", dst_dir)

    if request.method == 'POST':
        img_name = request.form.get('fav_img')
        delete_img = request.form.get('delete_img')

        if img_name:
            print("KEEP")
            file_prefix = os.path.splitext(img_name)[0]


            for file_name in glob.glob(f"{src_dir}/{file_prefix}.*"):
                base_name = os.path.basename(file_name)
                name, ext = os.path.splitext(base_name)

                # Check and rename if file already exists
                counter = 1
                new_name = f"{dst_dir}/{name}{ext}"
                while os.path.exists(new_name):
                    new_name = f"{dst_dir}/{name}({counter}){ext}"
                    counter += 1

                shutil.move(file_name, new_name)
                print("MV", file_name, new_name)
            return ""
        elif delete_img:
            print("DELETE")
            file_prefix = os.path.splitext(delete_img)[0]

            for file_name in glob.glob(f"{src_dir}/{file_prefix}.*"):
                os.remove(file_name)
            return ""

        return redirect(url_for('home'))

    img_files = sorted([os.path.join('/', f) for f in os.listdir(src_dir) if f.endswith('.png')], key=lambda x: os.path.getmtime(src_dir + x))
    image_count = len(img_files)

    return render_template('index.html', img_files=img_files, image_count=image_count)

@app.route('/<path>.png')
def send_img(path):
    src_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    print("SEND", os.getcwd()+"/"+src_dir+"/"+path+".png", os.path.exists(os.getcwd()+"/"+src_dir+"/"+path+".png"))
    return send_from_directory(os.getcwd()+"/"+src_dir, path+".png")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8667, debug=True)

