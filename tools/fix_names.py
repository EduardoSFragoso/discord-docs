"""Corrige os nomes de arquivos extraidos do data.grf (kRO Latam).

O GRF guarda os nomes em bytes EUC-KR (coreano), mas o GRF Editor os
decodificou como CP1252 (codepage do Windows em pt-BR) ao extrair.
O caminho de volta e: nome_atual (str) -> encode cp1252 -> decode euc-kr.

Uso (rode com Python 3.x):
    python fix_names.py <pasta>            # dry-run: so mostra o plano
    python fix_names.py <pasta> --apply    # renomeia de verdade

Renomeia de baixo pra cima (arquivos antes das pastas). Nomes que
sobrevivem ao roundtrip identicos ficam como estao; falhas de encode
(bytes cp1252 indefinidos, raros) sao contadas e puladas.

Refazendo o sentido contrario se algo der errado: encode euc-kr,
decode cp1252.
"""
import os
import sys


def fix_name(name):
    if all(ord(c) < 128 for c in name):
        return name
    try:
        fixed = name.encode("cp1252").decode("euc_kr")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return None
    return fixed if fixed != name else name


def main():
    if len(sys.argv) < 2:
        sys.exit(f"uso: {sys.argv[0]} <pasta> [--apply]")
    root = sys.argv[1]
    apply = "--apply" in sys.argv[2:]

    total = fixed = skipped = unchanged = 0
    renames = []
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        for old in filenames + dirnames:
            total += 1
            new = fix_name(old)
            if new is None:
                skipped += 1
                continue
            if new == old:
                unchanged += 1
                continue
            renames.append((os.path.join(dirpath, old),
                            os.path.join(dirpath, new)))
            fixed += 1

    renames.sort(key=lambda r: r[0].count(os.sep), reverse=True)
    # o console do Windows em pt-BR nao imprime koreano: o relatorio
    # detalhado (quem vira o que) vai pra fix_names_report.txt em UTF-8
    report = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "fix_names_report.txt")
    with open(report, "w", encoding="utf-8") as rep:
        for src, dst in renames:
            rep.write(f"{src}  ->  {dst}\n")
            if apply:
                if os.path.exists(dst):
                    rep.write(f"!! destino existe, pulado: {dst}\n")
                    skipped += 1
                    continue
                os.rename(src, dst)

    modo = "RENOMEADO" if apply else "DRY-RUN (use --apply)"
    print(f"[{modo}] total={total} renomear={fixed} "
          f"inalterados={unchanged} pulados={skipped}")
    print(f"relatorio: {report}")


if __name__ == "__main__":
    main()
