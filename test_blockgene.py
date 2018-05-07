import unittest
from AngryBirdsGA.BlockGene import BlockGene

class TestBlockGene(unittest.TestCase):

    def setUp(self):
        self.gene = BlockGene( type=1, pos=[0,0], r=1)

    def test_should_initialize_gene_OK(self):
        self.assertIsInstance(self.gene, BlockGene, "Object created")
        print(self.gene.corners())


            
if __name__ == '__main__':
    unittest.main()
