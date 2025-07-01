from pathlib import Path
from typing import Annotated
import typer
import requests
import jinja2
import yaml

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader


app = typer.Typer()


@app.command()
def fetch(
    classname: Annotated[
        str, typer.Argument(help="The class to download the documentation")
    ],
    dir: Annotated[
        str, typer.Argument(help="The directory to download the documentation page")
    ],
    filename: Annotated[
        str, typer.Option("--name", "-n", help="The name of the generated file")
    ] = "",
    datatype: Annotated[
        bool,
        typer.Option(
            "--data", "-d", help="Fetch a datatype class instead of a class page"
        ),
    ] = False,
):
    """Download the Roblox documentation of a class for further usage.\n
    Note: It's REQUIRED to run this command before generating C++ headers or running other commands which depend on a downloaded doc page.
    """
    if filename:
        name = filename
    else:
        name = classname
    path = Path(dir) / f"{name}.yaml"
    if datatype:
        response = requests.get(
            "https://cdn.jsdelivr.net/gh/Roblox/creator-docs@master/content/en-us/reference/engine/datatypes/"
            + classname
            + ".yaml"
        )
    else:
        response = requests.get(
            "https://cdn.jsdelivr.net/gh/Roblox/creator-docs@master/content/en-us/reference/engine/classes/"
            + classname
            + ".yaml"
        )
    page = response.content
    with open(path, "wb") as f:
        f.write(page)


@app.command()
def generate(
    file: Annotated[
        str, typer.Argument(help="The YAML downloaded with `fetch` command")
    ],
    dir: Annotated[str, typer.Argument(help="Directory to put the generated header")],
    classname: Annotated[
        str,
        typer.Option(
            "--class",
            "-c",
            help="The name of the generated class",
            show_default="Class name in file",
        ),
    ] = "",
    filename: Annotated[
        str,
        typer.Option(
            "--name",
            "-n",
            help="The name of the generated header",
            show_default="The name of the input file",
        ),
    ] = "",
):
    """Generate a C++ header from a fetched YAML file"""
    path = Path(file)
    with open(path, "rb") as f:
        text = f.read()
    data = yaml.load(text, SafeLoader)

    if data["type"] == "datatype":
        isclass = False
    else:
       isclass = True

    if classname:
        name = classname
    else:
        name = data["name"] 

    def luatocpp(input):
        if input == "number":
            return "double"
        else:
            return input

    env = jinja2.Environment(
        loader=jinja2.PackageLoader("rblxapi2cpp", "."),
    )
    env.filters["luatocpp"] = luatocpp
    if isclass:
        template = env.get_template("class.hpp.jinja")
    else:
        template = env.get_template("datatype.hpp.jinja")
    if isclass:
        context = {
            "classname": name,
            "prop": data["properties"]
        }
    else:
        context = {
            "classname": name,
            "constrs": data["constructors"],
            "props": data["properties"]
        }
    if filename:
        outpath = Path(dir) / f"{filename}.hpp"
    else:
        outpath = Path(dir) / f"{path.stem}.hpp"
    with open(outpath, "w") as f:
        f.write(template.render(context))

if __name__ == "__main__":
    app()
