# Lógica proposicional

## Fórmulas

Las fórmulas se definen de forma recursiva y por casos:

- Una *variable* es una fórmula. Las variables se identifican y distinguen con
  letras mayúsculas (formalmente habría que considerar lenguaje y un conjunto de
  símbolos). Se llaman variables porque se les pueden asignar valores de verdad
  distintos: a las variables se les pueden asignar valores booleanos 
  (*verdadero* o *falso*).

- Una *constante* es una fórmula. Se identifica también con una letra mayúscula.
  En nuestro caso estamos considerando las constantes `T`, con valor semántico
  *verdadero*, y `F`, con valor semántico *falso*. Para que no haya confilctos
  con las variables, se añade la restrucción de que los símbolos `T` y `F` no se
  puedan usar para nombrar variables.

- Una *negación* es una fórmula que se define recursivamente a partir de otra
  fórmula dada (operador unario). La negación invierte el valor semántico de la
  fórmula a la que se aplica: si la fórmula toma el valor *verdadero*, la 
  negación toma el valor *falso*; si el valor es *falso*, toma el valor
  *verdadero*.
