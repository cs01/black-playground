#!/usr/bin/env python3
import os
import json
import base64
import lzma
import black
import dis

from flask import (
    Flask,
    render_template,
    request,
    send_from_directory,
    render_template_string,
    redirect,
    url_for,
)

app = Flask(__name__)


def compress_state(data):
    compressed = lzma.compress(json.dumps(data).encode("utf-8"))
    return base64.urlsafe_b64encode(compressed).decode("utf-8")


def decompress_state(state):
    compressed = base64.urlsafe_b64decode(state)
    return json.loads(lzma.decompress(compressed))


def format_code(source, line_length, skip_string_normalization, py36, pyi):
    try:
        mode = black.FileMode.from_configuration(
            py36=py36,
            pyi=pyi,
            skip_string_normalization=skip_string_normalization)
        formatted = black.format_str(
            source, line_length=line_length, mode=mode)
    except Exception as exc:
        formatted = exc

    return formatted


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"), "favicon.ico")


@app.route("/", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        source = request.form["source"]
        line_length = int(request.form["line_length"])
        skip_string_normalization = bool(
            request.form.get("skip_string_normalization"))
        py36 = bool(request.form.get("py36"))
        pyi = bool(request.form.get("pyi"))

        state = compress_state({
            "sc": source,
            "ll": line_length,
            "ssn": skip_string_normalization,
            "py36": py36,
            "pyi": pyi,
        })

        return redirect(url_for(".index", state=state))

    state = request.args.get("state")

    if not state:
        source = render_template("source.py")
        line_length = 60
        skip_string_normalization = False
        py36 = False
        pyi = False

        state = compress_state({
            "sc": source,
            "ll": line_length,
            "ssn": skip_string_normalization,
            "py36": py36,
            "pyi": pyi,
        })

        return redirect(url_for(".index", state=state))

    state = decompress_state(state)
    source = state.get("sc")
    line_length = state.get("ll")
    skip_string_normalization = state.get("ssn")
    py36 = state.get("py36")
    pyi = state.get("pyi")

    try:
        bytecode = dis.code_info(source) + "\n\n\n" + dis.Bytecode(
            source).dis()
    except SyntaxError as e:
        bytecode = str(e)

    data = {
        "source_code": source,
        "bytecode": bytecode,
        "options": {
            "line_length": line_length,
            "skip_string_normalization": skip_string_normalization,
            "py36": py36,
            "pyi": pyi,
        },
        "black_version": black.__version__,
    }

    return render_template("index.html", **data)


if __name__ == "__main__":
    app.run(debug=True)
