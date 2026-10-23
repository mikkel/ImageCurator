from pathlib import Path
import hmac
import os
import secrets
import shutil
import sys

from flask import Flask, abort, redirect, render_template, request, send_from_directory, session, url_for

app = Flask(__name__, static_url_path='/assets', static_folder='assets')
app.secret_key = secrets.token_bytes(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict')


def source_directory():
    return Path(sys.argv[1] if len(sys.argv) > 1 else os.getcwd()).resolve()


def selected_files(directory, filename):
    # Literal basenames only: never interpret user input as a path or glob.
    if not filename or '/' in filename or '\\' in filename or filename in ('.', '..'):
        abort(400)
    prefix = Path(filename).stem
    if not prefix or prefix in ('.', '..'):
        abort(400)
    return [p for p in directory.iterdir()
            if p.stem == prefix and p.is_file() and not p.is_symlink()]


@app.route('/', methods=['GET', 'POST'])
def home():
    src_dir = source_directory()
    if request.method == 'POST':
        expected = session.get('csrf_token', '')
        supplied = request.form.get('csrf_token', '')
        if not expected or not hmac.compare_digest(expected, supplied):
            abort(403)
        img_name = request.form.get('fav_img')
        delete_img = request.form.get('delete_img')
        if img_name and delete_img:
            abort(400)
        if img_name:
            dst_dir = Path(sys.argv[2] if len(sys.argv) > 2 else 'keep').resolve()
            dst_dir.mkdir(parents=True, exist_ok=True)
            for file_name in selected_files(src_dir, img_name):
                counter = 1
                new_name = dst_dir / file_name.name
                while new_name.exists() or new_name.is_symlink():
                    new_name = dst_dir / f'{file_name.stem}({counter}){file_name.suffix}'
                    counter += 1
                shutil.move(file_name, new_name)
            return ''
        if delete_img:
            for file_name in selected_files(src_dir, delete_img):
                file_name.unlink()
            return ''
        return redirect(url_for('home'))
    session.setdefault('csrf_token', secrets.token_urlsafe(32))
    files = [f for f in src_dir.iterdir() if f.suffix == '.png' and f.is_file() and not f.is_symlink()]
    files.sort(key=lambda f: f.stat().st_mtime)
    return render_template('index.html', img_files=['/' + f.name for f in files],
                           image_count=len(files), csrf_token=session['csrf_token'])


@app.route('/<path>.png')
def send_img(path):
    selected_files(source_directory(), path + '.png')
    candidate = source_directory() / (path + '.png')
    if candidate.is_symlink():
        abort(404)
    return send_from_directory(source_directory(), path + '.png')


if __name__ == '__main__':
    # This local file-management tool has no remote authentication boundary.
    app.run(host='127.0.0.1', port=8667, debug=False)
