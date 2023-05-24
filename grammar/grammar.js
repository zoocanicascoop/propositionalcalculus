// TODO
// - Add support for comments

module.exports = grammar({
  name: 'propositionalcalculus',


  rules: {
    file: $ => choice(
        $.examples,
        $.rules,
        $._proofs,
    ),


    examples: $ => seq(
      /Examples?:?/, 
      repeat($.formula)
    ),

    rules: $ => seq(
      /Rules?:?/,
      repeat1($.rule_declaration),
    ),

    _proofs: $ => seq(
      choice($.rules, $.rule_import),
      repeat1($.proof)
    ),

    proof: $ => seq(
      /Prove:?/, 
      $._proof_statement,
      field('steps', $._proof_steps_block),
    ),

    rule_import: $ => seq(
        "Rules from ",
        /[a-zA-Z0-9]+/
    ),

    rule_declaration: $ => seq(
        field('id', $.rule_id),
        ':',
        field('assumptions', choice($.formula, $._inline_formula_list)),
        choice('⊢', '|-'),
        field('conclusion', $.formula),

    ),

    rule_id: _ => /[A-Z0-9]+/,

    _proof_statement: $ => choice(
        seq(
          field('conclusion', $.formula),
          "from",
          field('assumptions', choice($.formula, $._inline_formula_list)),
        ),
        seq(
          field('assumptions', choice($.formula, $._inline_formula_list)),
          choice('⊢', '|-'),
          field('conclusion', $.formula)
        ),
    ),

    _proof_steps_block: $ => seq(
        "{", 
        repeat(seq(optional(/[0-9]+\. /), choice($.axiom_specialization, $.rule_application, $.sorry))), 
        "}"
    ),
    
    axiom_specialization: $ => seq("A: ", $.num, $.binding),
    rule_application: $ => seq("R: ", choice(
        seq($.rule_id, repeat($.num), $.binding),
        seq($.rule_id, repeat1($.num), optional($.binding)),
    )),

    num: _ => /[0-9]+/,
    sorry: $ => token("sorry"),

    _inline_formula_list: $ => seq( "[", $.formula, repeat(seq(',', $.formula)), "]"),

    binding: $ => seq("{", $.var_binding, repeat(seq(',', $.var_binding)), "}"),

    var_binding: $ => seq($.var, ":", $.formula),


    formula: $ => $._formula,

    _formula: $ => choice(
      $._atom,
      $._unary,
      $._binary,
    ),

    _atom: $ => choice(
      $.var,
      $.const,
    ),

    _unary: $ => choice(
        $.neg
    ),

    _binary: $ => choice(
        $.and,
        $.or,
        $.imp,
        seq("(", $._formula, ")")
    ),

    var: _ => /([A-EG-SU-Z])/,
    const: _ => /T|F/,

    neg: $ => prec.right(4, seq(choice('¬', '~', 'neg'), $._formula)),

    imp: $ => prec.right(0, seq(field("left", $._formula), choice("→", ">>", "imp"), field("right", $._formula))),
    and: $ => prec.left(2,  seq(field("left", $._formula), choice("∧", "&",  "and"), field("right", $._formula))),
    or:  $ => prec.left(1,  seq(field("left", $._formula), choice("∨", "|",  "or" ), field("right", $._formula))),




  }
});

