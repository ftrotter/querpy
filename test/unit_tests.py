import unittest as ut
import re
from querpy import Query, QueryComponent, SelectComponent, JoinComponent


class TestQueryComponent(ut.TestCase):

    def setUp(self):
       self.spaces = QueryComponent('COMMAND')
       self.commas = QueryComponent('COMMAND', ',')
       self.items = ['col1', 'col2', 'col3']

    def test_init(self):
        for comp, sep in zip([self.spaces, self.commas], [' ', ', ']):
            self.assertEqual(comp.header, 'COMMAND ')
            self.assertEqual(comp.components, [])
            self.assertEqual(comp.sep, sep)

    def test_empty_object_print(self):
        self.assertEqual(self.spaces(), '')

    def test_nonempty_object_print(self):
        self.spaces += 'some stuff'
        self.assertNotEqual(self.spaces(), '')
        self.assertEqual(self.spaces(), self.spaces.header + 'some stuff')

    def test_add_list_spaces(self):
        self.spaces += self.items
        self.assertEqual(self.spaces(), 
                         self.spaces.header + ' '.join(self.items))

    def test_add_list_commas(self):
        self.commas += self.items
        self.assertEqual(self.commas(),
                         self.commas.header + ', '.join(self.items))

    def test_add_single_spaces_and(self):
        self.commas += 'some stuff'
        self.assertEqual(self.commas(), 
                         self.commas.header + 'some stuff')

    def test_add_list_spaces_and(self):
        self.spaces += 'col0'
        self.spaces &= self.items
        self.assertEqual(
            self.spaces(), 
            self.spaces.header + 'col0 AND ' + ' AND '.join(self.items)
        )

    def test_add_list_commas_and(self):
        self.commas += 'col0'
        self.commas &= self.items
        self.assertEqual(
            self.commas(),
            self.commas.header + 'col0, AND ' + ', AND '.join(self.items)
        )

    def test_add_single_spaces_or(self):
        self.commas += 'some stuff'
        self.assertEqual(self.commas(), 
                         self.commas.header + 'some stuff')

    def test_add_list_spaces_or(self):
        self.spaces += 'col0'
        self.spaces |= self.items
        self.assertEqual(
            self.spaces(), 
            self.spaces.header + 'col0 OR ' + ' OR '.join(self.items)
        )

    def test_add_list_commas_or(self):
        self.commas += 'col0'
        self.commas |= self.items
        self.assertEqual(
            self.commas(),
            self.commas.header + 'col0, OR ' + ', OR '.join(self.items)
        )

    def test_add_wrong_type_raises_ValueError(self):
        # want to keep __add_item private, so workaround to test error:
        def is_error(val):
            try:
                self.commas += val
            except ValueError:
                raise ValueError

        self.assertRaises(ValueError, is_error, 5)

    def test_clear(self):
        self.commas += self.items
        self.commas.clear()
        self.assertEqual(self.commas(), '')


class TestSelectComponent(ut.TestCase):
    
    def setUp(self):
        self.comp = SelectComponent('SELECT')
        self.items = ['col1', 'col2', 'col3']

    def test_init(self):
        for attr, val in zip(
            [self.comp.header, self.comp.components, self.comp.dist,
             self.comp.topN, self.comp.sep],
            ['SELECT ', [], False, False, ', ']
        ):
            self.assertEqual(attr, val)

    def test_distinct_regex(self):
        string = 'SELECT DISTINCT TOP 1000'
        subbed = re.sub(self.comp.dist_pattern, '', string)
        # nb. extra space is fine here--stripped out at Query level
        self.assertEqual(subbed, 'SELECT TOP 1000')

    def test_top_regex(self):
        string = 'SELECT TOP 5000 DISTINCT'
        subbed = re.sub(self.comp.top_pattern, '', string)
        # nb. extra space is fine here--stripped out at Query level
        self.assertEqual(subbed, 'SELECT DISTINCT')

    def test_distinct_False_to_True(self):
        self.comp.distinct = True
        self.assertEqual(self.comp(), '')
        self.comp += 'col2'
        self.assertEqual(self.comp(), 'SELECT DISTINCT col2')

    def test_distinct_True_to_False(self):
        self.comp.distinct = True
        self.assertEqual(self.comp(), '')
        self.comp += 'col2'
        self.assertEqual(self.comp(), 'SELECT DISTINCT col2')
        self.comp.distinct = False
        self.assertEqual(self.comp(), 'SELECT col2')

    def test_top_False_to_val(self):
        self.comp.top = 5
        self.assertEqual(self.comp(), '')
        self.comp += 'col2'
        self.assertEqual(self.comp(), 'SELECT TOP 5 col2')

    def test_top_val_to_False(self):
        self.comp.top = 5
        self.assertEqual(self.comp(), '')
        self.comp += 'col2'
        self.assertEqual(self.comp(), 'SELECT TOP 5 col2')
        self.comp.top = False
        self.assertEqual(self.comp(), 'SELECT col2')

    def test_distinct_top_set_wrong_type_raises_ValueError(self):
        self.assertRaises(ValueError, self.comp.__setattr__, 'distinct', 5)
        self.assertRaises(ValueError, self.comp.__setattr__, 'top', '5')

    def test_clear_resets_distinct_top(self):
        self.comp.top = 5
        self.comp.distinct = True
        self.comp.clear()
        self.assertFalse(self.comp.distinct)
        self.assertFalse(self.comp.top)


class TestJoinComponent(ut.TestCase):

    def test_call_adds_joins(self):
        join = JoinComponent('JOIN')
        join += 'tbl1 ON var1 = other1'
        join += 'tbl2 ON var2 = other2'
        self.assertEqual(
            join(), 'JOIN tbl1 ON var1 = other1 JOIN tbl2 ON var2 = other2'
        )


class TestQuery(ut.TestCase):

    def setUp(self):
        self.query = Query()

    def test_init(self):
        attrs = ['s', 'f', 'j', 'w', 'g']
        classes = [SelectComponent, QueryComponent, JoinComponent,
                   QueryComponent, QueryComponent]
        com = ', '
        spc = ' '
        seps = [com, spc, spc, spc, com] 
        for a, c in zip(attrs, classes):
            self.assertTrue(
                isinstance(getattr(self.query, a), c),
                'self.query.{a} is not an instance of {c}'.format(
                    a = a, c = c.__name__
                )
            )
        for a, s in zip(attrs, seps):
            self.assertEqual(getattr(self.query, a).sep, s,
                             'self.query.{a}.sep != {s})'.format(
                                 a = a, s = s
                             ))

    def test_regex(self):
        string = '  leading space and  spaces    and trailing spaces      '
        subbed = re.subn(self.query.pattern, '', string)[0]
        self.assertEqual(subbed, 
                         'leading space and spaces and trailing spaces')

    def test_statement(self):
        self.query.s += ['col1', 'col2']
        self.query.f += 'dbo.a_table'
        self.query.j += 'dbo.b_table ON a_table.id = b_table.id'
        self.query.w += 'col1 IS NOT NULL'
        self.query.g += ['col1', 'col2']
        self.assertEqual(
            self.query.statement,
            'SELECT col1, col2 FROM dbo.a_table '
            'JOIN dbo.b_table ON a_table.id = b_table.id '
            'WHERE col1 IS NOT NULL '
            'GROUP BY col1, col2'
        )

    def test_distinct(self):
        self.query.distinct = True
        self.assertTrue(self.query.distinct)
        self.query.s += 'hello'
        self.assertEqual(self.query.statement, 'SELECT DISTINCT hello')
        self.query.distinct = False
        self.assertFalse(self.query.distinct)
        self.assertEqual(self.query.statement, 'SELECT hello')

    def test_top(self):
        self.query.top = 10
        self.assertEquals(self.query.top, 10)
        self.query.s += 'hello'
        self.assertEqual(self.query.statement, 'SELECT TOP 10 hello')
        self.query.top = False
        self.assertFalse(self.query.top)
        self.assertEqual(self.query.statement, 'SELECT hello')


if __name__ == '__main__':

    ut.main()