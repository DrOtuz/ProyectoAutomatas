# Entregables

`Entregables.zip` está dividido en partes de menos de 100 MB porque GitHub no admite archivos más grandes. Contiene el banner del proyecto, los documentos de exposición (Grupos A, B y C), el seguimiento y notas, y el video de funcionamiento.

## Unir las partes

Windows (símbolo del sistema, dentro de esta carpeta):

```bat
copy /b Entregables.zip.001+Entregables.zip.002 Entregables.zip
```

Linux o macOS:

```bash
cat Entregables.zip.* > Entregables.zip
```

Después se descomprime `Entregables.zip` de la forma habitual.
