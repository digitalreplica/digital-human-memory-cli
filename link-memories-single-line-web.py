import hashlib
import itertools
import re
import os
import sys

MEMORY_DIR = 'memory'
THREAD_DIR = 'threads'
MULTI_THREAD_DIR = '.threads'
VERBOSE = True

##### MemoryPage #####
class MemoryPage:
    '''
    Everything related to a single page
    '''
    def __init__(self, filepath):
        # Create a MemoryPage, given it's filepath. Can be absolute or relative path, named like <guid>.md
        self.filepath = filepath
        basepath = os.path.basename(filepath)
        self.id = os.path.splitext(basepath)[0] # id is the basename without extension, should be a guid

        # Read first line of file to extract title. Remove leading hash symbols and spaces
        with open(filepath) as f:
            self.title = f.readline().rstrip().lstrip('#').lstrip()

        # Extract the concepts from the title
        self.extract_concepts_from_title()

        # Print
        if VERBOSE:
            print("  {} ({}) {}".format(self.title, self.id, str(self.concepts)))

    def extract_concepts_from_title(self):
        '''
        Extract the concepts from the title. A concept is in markdown italics, without spaces.
            *Favorite* Food: returns ['Favorite']
            *Favorite Stuff*: returns [], because of the space
        :param title: String title of page
        :return: all concepts as an list of strings
        '''
        self.concepts = []
        for word in self.title.split():
            if word.startswith('*') and word.endswith('*'):
                concept = word.replace('*', '')
                self.concepts.append(concept)

    def update_memory_links(self, memory_threads):
        '''
        STILL NEEDS WORK
        :param memory_threads:
        :return:
        '''
        reverse_link_regex = re.compile(r'\(\.\/'+MEMORY_DIR+r'\/[-0-9a-f]*?\.md\)')
        with open(self.filepath) as f:
            for line in f:
                line = line.rstrip()
                m = reverse_link_regex.match(line)
                if m:
                    print(m)


##### MemoryThread #####
class MemoryThread:
    def __init__(self, concepts):
        self.concepts = concepts
        self.threads = []
        self.pages = []
        self.is_single = False
        if len(concepts) == 1:
            self.is_single = True
        self.id = self.hash_concepts(self.concepts)

    @classmethod
    def hash_concepts(cls, concepts):
        '''
        Create a unique hash for a set of concepts, regardless of case or order
        :param concepts:
        :return:
        '''
        # Single concepts return the concept
        if len(concepts) == 1:
            return concepts[0]

        # Lowercase and sort
        sorted_concepts = [x.lower() for x in concepts]
        sorted_concepts.sort()

        # Return hash of joined concepts
        key = '|'.join(sorted_concepts).encode("utf-8")
        return hashlib.sha256(key).hexdigest()

    def add_page(self, page):
        if page not in self.pages:
            self.pages.append(page)

    def add_thread(self, thread):
        if thread not in self.threads:
            self.threads.append(thread)

    def diff_thread(self, thread):
        return list(set(self.concepts) - set(thread.concepts))

##### MemoryThreads #####
class MemoryThreads:
    def __init__(self, memory_repo_dir, dest_dir):
        # Set directories to use, creating if needed
        self.memory_repo_dir = memory_repo_dir
        self.memory_dir = os.path.join(self.memory_repo_dir, MEMORY_DIR)
        self.thread_dir = os.path.join(dest_dir, THREAD_DIR)
        create_directory(self.thread_dir)
        self.multi_thread_dir = os.path.join(dest_dir, MULTI_THREAD_DIR)
        create_directory(self.multi_thread_dir)

        self.memory_pages = []
        self.forward_links = {}  # links from title to file
        self.reverse_links = {}  # links from file to title
        self.threads = {}        # concept threads
        self.load_memory_files()

    def load_memory_files(self):
        if VERBOSE:
            print("Processing memory files")
        # Loop through all memory files
        for filename in os.listdir(self.memory_dir):
            # Only markdown files
            if not filename.endswith(".md"):
                continue

            # Save memory page
            memory_file = os.path.join(self.memory_dir, filename)
            memory_page = MemoryPage(memory_file)
            self.memory_pages.append(memory_page)

            # Add forward links to page using title
            if memory_page.title not in self.forward_links:
                self.forward_links[memory_page.title] = memory_page
            else:
                print("Duplicate title '{}' in files {} and {}".format(memory_page.title, filename,
                                                                       forward_links[memory_page.title]), file=sys.stderr)

            # Add reverse links to page using id
            self.reverse_links[memory_page.id] = memory_page

            # Create memory threads from concepts
            self.recurse_concepts(memory_page, memory_page.concepts, len(memory_page.concepts))

    def recurse_concepts(self, memory_page, concepts, depth, child_memory_thread=None):
        '''
        Recurse all combinations of concepts, creating a thread for the combination, and adding the page
        :param memory_page:
        :param concepts:
        :param depth: combination depth, recursing from largest to smallest
        :return:
        '''
        #memory_thread = self.get_thread(concepts)
        #memory_thread.add_page(memory_page)
        combinations = itertools.combinations(concepts, depth)
        for combination in combinations:
            memory_thread = self.get_thread(list(combination))
            memory_thread.add_page(memory_page)

            # Add child thread
            if child_memory_thread:
                memory_thread.add_thread(child_memory_thread)

            # Recurse while depth > 1
            if depth > 1:
                self.recurse_concepts(memory_page, list(combination), depth-1, memory_thread)
            pass

    def get_thread(self, concepts):
        '''
        Get or create a MemoryThread for set of concepts
        :param concepts: list of concepts
        :return: MemoryThread
        '''
        concept_hash = MemoryThread.hash_concepts(concepts)
        if concept_hash in self.threads:
            return self.threads[concept_hash]

        # Create new MemoryThread
        memory_thread = MemoryThread(concepts)
        self.threads[concept_hash] = memory_thread
        return memory_thread

    def write_thread_markdown_files(self):
        '''
        For all threads, write out a markdown file with sub-concepts and pages
        :return:
        '''
        if VERBOSE:
            print("")
            print("Writing thread markdown files")

        # Loop over threads
        for thread_hash, thread in self.threads.items():
            # Open markdown file
            thread_path = self.get_thread_markdown_filepath(thread)
            with open(thread_path, 'w') as markdown_file:
                print("  {}".format(thread_path))
                markdown_file.write("# {}\n".format(' '.join(thread.concepts)))
                if thread.threads:
                    markdown_file.write("\n")
                    markdown_file.write("## Additional Threads\n")
                    for subthread in thread.threads:
                        diff = subthread.diff_thread(thread)
                        subthread_path = self.get_thread_markdown_filepath(subthread)
                        subthread_relative_path = os.path.relpath(subthread_path, start=os.path.dirname(thread_path))
                        markdown_file.write("* [{}]({})\n".format(diff[0], subthread_relative_path))

                if thread.pages:
                    markdown_file.write("\n")
                    markdown_file.write("## Pages\n")
                    for page in thread.pages:
                        page_relative_path = os.path.relpath(page.filepath, start=os.path.dirname(thread_path))
                        markdown_file.write("* [{}]({})\n".format(page.title, page_relative_path))

    def get_thread_markdown_filepath(self, thread: MemoryThread):
        '''
        Finds the file path for a given thread. Single threads go in THREAD_DIR. Multiple threads go in THREAD_DIR
        :param thread_hash: String. The thread_hash is used as the basename of the file
        :param thread: MemoryThread. Determines if thread is single or multiple
        :return: string file path
        '''
        if thread.is_single:
            return os.path.join(self.thread_dir, thread.id+".md")
        else:
            return os.path.join(self.multi_thread_dir, thread.id + ".md")

    def link_memories(self):
        '''
        Look through memory files for links to other memory files. Update links if needed.
        :return:
        '''

        # Loop across all pages
        if VERBOSE:
            print("")
            print("Updating memory links")
        for page in self.memory_pages:
            page.update_memory_links(self)

##### Standalone functions #####

def create_directory(dir):
    '''
    Creates a directory, if it doesn't exist
    :param dir:
    :return:
    '''
    if not os.path.isdir(dir):
        if VERBOSE:
            print("Making {}".format(dir))
        os.mkdir(dir)

##### Main program #####
if VERBOSE:
    print("Current directory: " + os.getcwd())
    print("")
memory_threads = MemoryThreads('.', '.')
memory_threads.write_thread_markdown_files()
memory_threads.link_memories()
pass
