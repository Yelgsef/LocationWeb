from __future__ import annotations

import os
import time
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, send_file, url_for

from function import POI, geocode

BASE_DIR = Path(__file__).resolve().parent
MAP_FILE = BASE_DIR / "output.html"


def create_app() -> Flask:
    app = Flask(__name__)
    # Simple secret key so we can use flash messages without extra setup.
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "POST":
            location = request.form.get("location", "").strip()
            if not location:
                flash("Vui lòng nhập địa điểm ở Việt Nam.", "danger")
                return redirect(url_for("index"))

            # Append "Việt Nam" to bias the geocoder to the country we care about.
            query = f"{location}, Việt Nam"
            try:
                lat, lon, display_name = geocode(query)
                POI(float(lat), float(lon), radius=1500, POI_count=5)
                flash(f"Đang hiển thị quán cà phê quanh {display_name}.", "success")
                return render_template(
                    "index.html",
                    map_ready=True,
                    display_name=display_name,
                    timestamp=int(time.time()),
                )
            except Exception as exc:  # Broad catch to surface friendly message.
                flash(f"Lỗi khi tìm địa điểm: {exc}", "danger")
                return redirect(url_for("index"))

        return render_template("index.html", map_ready=False)

    @app.route("/map")
    def map_view():
        if not MAP_FILE.exists():
            flash("Chưa có bản đồ nào được tạo.", "warning")
            return redirect(url_for("index"))
        return send_file(MAP_FILE)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
