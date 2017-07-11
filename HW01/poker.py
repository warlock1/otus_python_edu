#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -----------------
# Реализуйте функцию best_hand, которая принимает на вход
# покерную "руку" (hand) из 7ми карт и возвращает лучшую
# (относительно значения, возвращаемого hand_rank)
# "руку" из 5ти карт. У каждой карты есть масть(suit) и
# ранг(rank)
# Масти: трефы(clubs, C), пики(spades, S), червы(hearts, H), бубны(diamonds, D)
# Ранги: 2, 3, 4, 5, 6, 7, 8, 9, 10 (ten, T), валет (jack, J), дама (queen, Q), король (king, K), туз (ace, A)
# Например: AS - туз пик (ace of spades), TH - дестяка черв (ten of hearts), 3C - тройка треф (three of clubs)

# Задание со *
# Реализуйте функцию best_wild_hand, которая принимает на вход
# покерную "руку" (hand) из 7ми карт и возвращает лучшую
# (относительно значения, возвращаемого hand_rank)
# "руку" из 5ти карт. Кроме прочего в данном варианте "рука"
# может включать джокера. Джокеры могут заменить карту любой
# масти и ранга того же цвета, в колоде два джокерва.
# Черный джокер '?B' может быть использован в качестве треф
# или пик любого ранга, красный джокер '?R' - в качестве черв и бубен
# любого ранга.

# Одна функция уже реализована, сигнатуры и описания других даны.
# Вам наверняка пригодится itertoolsю
# Можно свободно определять свои функции и т.п.
# -----------------

import itertools

def hand_rank(hand):
    """Возвращает значение определяющее ранг 'руки'"""
    ranks = card_ranks(hand)
    if straight(ranks) and flush(hand):
        return (8, max(ranks))
    elif kind(4, ranks):
        return (7, kind(4, ranks), kind(1, ranks))
    elif kind(3, ranks) and kind(2, ranks):
        return (6, kind(3, ranks), kind(2, ranks))
    elif flush(hand):
        return (5, ranks)
    elif straight(ranks):
        return (4, max(ranks))
    elif kind(3, ranks):
        return (3, kind(3, ranks), ranks)
    elif two_pair(ranks):
        return (2, two_pair(ranks), ranks)
    elif kind(2, ranks):
        return (1, kind(2, ranks), ranks)
    else:
        return (0, ranks)


def card_ranks(hand):
    """Возвращает список рангов (его числовой эквивалент),
    отсортированный от большего к меньшему"""
    CARD_RANKS = {'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
    ranks = [CARD_RANKS[h[0]] if h[0] in CARD_RANKS else int(h[0]) for h in hand]
    ranks.sort(reverse=True)
    return ranks


def flush(hand):
    """Возвращает True, если все карты одной масти"""
    return len(set(v[1] for v in hand)) == 1


def straight(ranks):
    """Возвращает True, если отсортированные ранги формируют последовательность 5ти,
    где у 5ти карт ранги идут по порядку (стрит)"""
    sorted_ranks = sorted(ranks)
    CARDS_SEQ = 5
    for i in range(len(sorted_ranks) - (CARDS_SEQ - 1)):
        if sum(sorted_ranks[i+j]-sorted_ranks[i+j-1] for j in range(1, CARDS_SEQ)) == 4:
            return True
    return False


def kind(n, ranks):
    """Возвращает первый ранг, который n раз встречается в данной руке.
    Возвращает None, если ничего не найдено"""
    cnt = {}
    for r in ranks:
        cnt[r] = cnt.get(r, 0) + 1
    for r, c in cnt.items():
        if c == n:
            return r
    return None


def two_pair(ranks):
    """Если есть две пары, то возврщает два соответствующих ранга,
    иначе возвращает None"""
    cnt = {}
    for r in ranks:
        cnt[r] = cnt.get(r, 0) + 1
    result = tuple(r for r, c in cnt.items() if c == 2)
    return result if len(result) == 2 else None


def best_hand(hand):
    """Из "руки" в 7 карт возвращает лучшую "руку" в 5 карт """
    CARDS_SEQ = 5
    result = []
    for hand5 in itertools.combinations(hand, CARDS_SEQ):
        result.append((hand5, hand_rank(hand5)))
    return sorted(result, key=lambda v: v[1], reverse=True)[0][0]


def best_wild_hand(hand):
    """best_hand но с джокерами"""

    def gen_cards(joker, hand):
        RANKS_CARDS = {10: 'T', 11: 'J', 12: 'Q', 13: 'K', 14: 'A'}
        SUITS = ('C', 'S') if joker == '?B' else ('H', 'D')
        CARDS = (2, 15)
        return [c for c in
                [(str(c) if c not in RANKS_CARDS else RANKS_CARDS[c]) + s for s in SUITS for c in range(*CARDS)]
                if c not in hand]

    hand_n = []
    hand_j = []
    for c in hand:
        if c.startswith('?'):
            hand_j.append(gen_cards(c, hand))
        else:
            hand_n.append(c)
    if len(hand_j) == 0:
        return best_hand(hand_n)
    else:
        CARDS_SEQ = 5
        result = []
        for joker_cards in itertools.product(*hand_j):
            for hand5 in itertools.combinations(tuple(hand_n) + joker_cards, CARDS_SEQ):
                result.append((hand5, hand_rank(hand5)))
        return sorted(result, key=lambda v: v[1], reverse=True)[0][0]


def test_best_hand():
    print "test_best_hand..."
    assert (sorted(best_hand("6C 7C 8C 9C TC 5C JS".split()))
            == ['6C', '7C', '8C', '9C', 'TC'])
    assert (sorted(best_hand("TD TC TH 7C 7D 8C 8S".split()))
            == ['8C', '8S', 'TC', 'TD', 'TH'])
    assert (sorted(best_hand("JD TC TH 7C 7D 7S 7H".split()))
            == ['7C', '7D', '7H', '7S', 'JD'])
    print 'OK'


def test_best_wild_hand():
    print "test_best_wild_hand..."
    assert (sorted(best_wild_hand("6C 7C 8C 9C TC 5C ?B".split()))
            == ['7C', '8C', '9C', 'JC', 'TC'])
    assert (sorted(best_wild_hand("TD TC 5H 5C 7C ?R ?B".split()))
            == ['7C', 'TC', 'TD', 'TH', 'TS'])
    assert (sorted(best_wild_hand("JD TC TH 7C 7D 7S 7H".split()))
            == ['7C', '7D', '7H', '7S', 'JD'])
    print 'OK'


if __name__ == '__main__':
    test_best_hand()
    test_best_wild_hand()
