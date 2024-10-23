## Primeros pasos

### Gestor de paquetes *poetry*

El proyecto de python está gestionado con el gestor de paquetes de python
[*poetry*](https://python-poetry.org/). Puedes instalar *Poetry* mediante el
siguiente comando:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Si encuentras problemas con la instalación consulta la [documentación
oficial](https://python-poetry.org/docs/#installing-with-the-official-installer).

### Instalación de dependencias

Una vez clonado el repositorio *propositionalcalculus* en tu máquina, puedes
utilizar *poetry* para gestionar las dependencias y el entorno de desarrollo. 
Como otras utilidades de python, *poetry* instala los paquetes de los que depende
cada aplicación en un entorno virtual, asegurando que las dependencias se
instalan de manera aislada.

Para instalar las dependencias ejecuta

```bash
poetry install
```

### Entorno de desarrollo

Una vez instaladas las dependencias, puedes iniciar un entorno shell donde
estarán disponibles todos los paquetes necesarios para ejecutar y desarrollar el
programa.

```bash
poetry shell
```

Dentro de esta shell puedes ejecutar el módulo de python y las utilidades
asociadas. También ejecutar otras aplicaciones como tu editor, de forma que
estas se ejecuten teniendo acceso al entorno virtual.

### Ejecución

Para ejecutar la aplicación principal, que ejecutará la función *main*, debes
lanzar el siguiente comando desde la shell de *poetry*:
```bash
python3 -m propositionalcalculus
```

Si deseas ejecutar un comando en el entorno virtual de *poetry* pero sin entrar
en la shell, puedes usar `poetry run`. Por ejemplo:

```bash
poetry run python3 -m propositionalcalculus
```

En el entorno tienes disponibles otros comandos como *mkdocs* (para la gestión
de la documentación) y *pytest* (ejecución de tests), con sus subcomandos
asociados.
