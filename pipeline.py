from typing import List

from spiders import Spider


# sentences1: List[str], sentences2: List[str], model: nn.Sequential, batch_size: int = 32,
#                show_progress_bar: bool = None, output_value: str = 'sentence_embedding',
#                convert_to_numpy: bool = True, convert_to_tensor: bool = False, is_pretokenized: bool = False,
#                device: str = "cpu", num_workers: int = 4

def pipline(spiders: List[Spider], starting_points: List[str], show_progress_bar: bool = False):
    """
    execute spiders in loop
    :param spiders:
    :param starting_points:
    :return:
    """

    for ix, spider in enumerate(spiders):
        spider.query(starting_points)

