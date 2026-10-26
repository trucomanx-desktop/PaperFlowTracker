# paper-flow-tracker

Follow each stage of the process of publishing scientific articles

## Upload to PYPI

```bash
pip install --upgrade pkginfo twine packaging

cd src
python -m build
twine upload dist/*
```
