from flask import Flask
from flask import g, make_response, Response, request, session, render_template
import pandas as pd
from pathlib import Path

DEFAULT_PAGE_SIZE = 3
DEFALUT_BLOCK_SIZE = 10


class Page:
    def __init__(self, index):
        self.index = index
        self.href = ""


class Paging:
    def __init__(self, page_size, current_index, total_rows):
        self.page_size = total_rows if page_size == 0 else page_size
        self.current_index = current_index
        self.total_rows = total_rows
        self.start_index = 0
        self.end_index = 0
        self.last_index = 0
        self.first_page = None
        self.last_page = None
        self.previous_page = None
        self.next_page = None
        self.pages = list()
        self.set_pages()

    def paging_value(self, page_size, current_index, total_rows):
        self.page_size = total_rows if page_size == 0 else page_size
        self.current_index = current_index
        self.total_rows = total_rows
        set_pages(self)

    def get_start_row(self):
        if self.current_index <= 0:
            current_index = 1
        return int((self.current_index - 1) * self.page_size)

    def get_next_page_row(self):
        return get_start_row() + page_size

    def find_start_end_index(self):
        interval = DEFALUT_BLOCK_SIZE
        self.last_index = int(self.total_rows / self.page_size)
        if self.total_rows % self.page_size > 0:
            self.last_index += 1
        self.start_index = 1

        while True:
            self.end_index = self.start_index + interval - 1
            if (
                self.current_index >= self.start_index
                and self.current_index <= self.end_index
                and self.end_index <= self.last_index
            ):
                break
            if self.end_index > self.last_index:
                self.end_index = self.last_index
                break
            self.start_index = self.end_index + 1

        self.end_index = 1 if self.end_index == 0 else self.end_index

    def set_pages(self):
        self.find_start_end_index()
        for i in range(int(self.start_index), int(self.end_index) + 1):
            self.pages.append(Page(i))

        self.first_page = Page(self.start_index)
        self.last_page = Page(self.last_index)

        if self.current_index - 1 > 0:
            self.previous_page = Page(self.current_index - 1)
        else:
            self.previous_page = self.first_page

        if (
            self.current_index + 1 < self.end_index
            or self.current_index + 1 < self.last_index
        ):
            self.next_page = Page(self.current_index + 1)
        else:
            self.next_page = self.last_page
