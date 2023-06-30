
def asciiQr(code):
    import segno
    import io
    qrcode = segno.make(code)
    out = io.StringIO()
    # qrcode.terminal(out=out, border=1, compact=True)
    qrcode.terminal(out=out, border=1)
    out.seek(0)
    result = out.read()
    return result
