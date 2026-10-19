## Qué cambia
<!-- Una o dos frases. Qué hace este PR y por qué. -->

## Tarea y requisitos
- Tarea: <!-- por ejemplo A-13 -->
- Requisitos que cubre: <!-- por ejemplo RF-14, RNF-03 -->

## Antes de pedir revisión
- [ ] `ruff check .` sin avisos
- [ ] `pytest` en verde
- [ ] `lint-imports` en verde (`1 kept, 0 broken`)
- [ ] Cada comportamiento nuevo tiene prueba con `@pytest.mark.requisito(...)`
- [ ] Nombres en español sin tildes ni eñes (clases `PascalCase`, métodos `camelCase`, variables `snake_case`)

## Contratos
- [ ] Este PR **no** cambia ningún contrato (`src/simulador/contratos/` ni `docs/contratos.md`)
- [ ] Este PR **sí** cambia un contrato: describí el cambio abajo y pedí la aprobación de los tres líderes

<!-- Si cambia un contrato: qué cambia, quién lo usa y qué debe hacer cada subgrupo. -->

## Quién debe revisar
<!-- Usuario(s) de GitHub, por ejemplo @usuario. -->

## Notas para quien revisa
<!-- Dudas, decisiones tomadas, cosas que no se hicieron a propósito. Puede quedar vacío. -->

---
Fusionar con **"Create a merge commit"** (sin squash ni rebase).