# rows2prose

Display visual blocks of text with data rendered inline.

Many visualizations can be built as follows:

1. Create a list of table/database rows (a.k.a. a dataframe)
2. Create a block of styled text that refers to that dataframe's columns
3. Render those columns into the text

For example, you might snapshot the state of a system and store it as a row in a table. You can trace the system over time, or across experiments, building up a single table, indicating each row's time in a dedicated "i_timestep" column, or experiment in a "i_config" column. The columns of this table can then be easily rendered into an appropriate visualization.

The vision for rows2prose is to bring this workflow to Python, R, and other languages that are not JavaScript. (JavaScript programmers are fine, they don't need rows2prose.)