import os, json, base64, random, colorsys
from io import BytesIO
from PIL import Image, ImageDraw, ImageChops
from dash import Dash, html, dash_table, Input, Output


# ---------------- Image Generation ----------------
def random_point(size, padding=5):
    return random.randint(padding, size - padding)


def random_color():
    h = random.random()
    r, g, b = colorsys.hsv_to_rgb(h, 1, 1)
    return int(r * 255), int(g * 255), int(b * 255)


def interpolate(c1, c2, f):
    return tuple(int((1 - f) * a + f * b) for a, b in zip(c1, c2))


def generate_art(size=128):
    points = [(random_point(size), random_point(size)) for _ in range(5)]
    start_color, end_color = random_color(), random_color()
    image = Image.new("RGB", (size, size), (0, 0, 0))
    for i, p in enumerate(points):
        overlay = Image.new("RGB", (size, size), (0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        next_p = points[0] if i == len(points) - 1 else points[i + 1]
        draw.line([p, next_p], fill=interpolate(start_color, end_color, i / 4), width=2)
        image = ImageChops.add(image, overlay)
    buff = BytesIO()
    image.save(buff, format="WEBP", quality=70)
    return base64.b64encode(buff.getvalue()).decode()


# ---------------- Dash App ----------------
def launch_app(total_images=1000, page_size=10):
    app = Dash(__name__)

    # In-memory cache
    cache = {}

    app.layout = html.Div(
        [
            dash_table.DataTable(
                id="datatable-pagination",
                columns=[{"name": "id", "id": "id"}],
                page_current=0,
                page_size=page_size,
                page_action="custom",
            ),
            html.Div(
                id="nft-container",
                style={"display": "flex", "flexWrap": "wrap", "marginTop": "20px"},
            ),
        ]
    )

    def get_page_images(page):
        if page in cache:
            return cache[page]
        start = page * page_size
        end = min(start + page_size, total_images)
        images = [generate_art() for _ in range(end - start)]
        cache[page] = images
        return images

    @app.callback(
        Output("datatable-pagination", "data"),
        Output("nft-container", "children"),
        Input("datatable-pagination", "page_current"),
        Input("datatable-pagination", "page_size"),
    )
    def update(page_current, page_size):
        images = get_page_images(page_current)
        children = [
            html.Div(
                [
                    html.P(f"ID: {page_current * page_size + i + 1}"),
                    html.Img(
                        src=f"data:image/webp;base64,{img}",
                        style={
                            "width": "128px",
                            "border": "1px solid blue",
                            "margin": "5px",
                        },
                    ),
                ]
            )
            for i, img in enumerate(images)
        ]
        data = [{"id": page_current * page_size + i + 1} for i in range(len(images))]
        return data, children

    return app


# ---------------- Run ----------------
import os

if __name__ == "__main__":
    app = launch_app()
    # Use the Replit provided PORT
    port = int(os.environ.get("PORT", 3000))  # 3000 is default fallback
    app.run(debug=False, host="0.0.0.0", port=port)
