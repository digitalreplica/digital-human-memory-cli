#!/usr/bin/env python3
import hashlib
import itertools
import os
import subprocess
import typer
import uuid
from contextlib import suppress

##### Globals #####
WEB_DIRECTORY = "web"
SYMLINK_DIRECTORY = "symlink"
VERBOSE = True

##### Utility functions #####
def copy_to_clipboard(text):
    """
    Copies the given text into the system clipboard
    :param text:
    :return:
    """
    subprocess.run("pbcopy", universal_newlines=True, input=text)

def open_file_in_editor(filename):
    """
    Opens a file in the preferred editor
    :param filename:
    :return:
    """
    subprocess.run(["atom", filename])

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

def create_symlink(symlink, target):
    '''
    Creates a symlink, if it doesn't exist
    :param symlink:
    :param target:
    :return:
    '''
    if not os.path.islink(symlink):
        print("  {} -> {}".format(symlink, target))
        os.symlink(target, symlink)

def search_files(directory='.', extension=''):
    filelist = []
    for dirpath, dirnames, files in os.walk(directory):
        for name in dirnames:
            filelist.append((os.path.join(dirpath, name)))
        for name in files:
            filelist.append((os.path.join(dirpath, name)))
    return filelist

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

##### MemoryConcept #####
class MemoryConcept:
    """
    A group of memory pages under the same set of concepts. Concepts can have sub-concepts.
    """
    def __init__(self, concepts):
        self.concepts: list = concepts
        self.subconcepts: MemoryConcept = []
        self.pages: MemoryPage = []
        self.is_single = False
        if len(concepts) == 1:
            self.is_single = True
        self.id = self.hash_concepts(self.concepts)

    @classmethod
    def hash_concepts(cls, concepts):
        '''
        Create a unique hash for a set of concepts, so pages can be added, regardless of case or order for the concepts
        :param concepts: List of (string) concepts
        :return: string
        '''
        # Single concepts return the concept
        if len(concepts) == 1:
            return concepts[0]

        # Lowercase and sort
        sorted_concepts = [x.capitalize() for x in concepts]
        sorted_concepts.sort()

        # Return hash of joined concepts
        #key = ''.join(sorted_concepts).encode("utf-8")
        key = ''.join(sorted_concepts)
        return key
        #return hashlib.sha256(key).hexdigest()

    def add_page(self, page):
        if page not in self.pages:
            self.pages.append(page)

    def add_subconcept(self, memory_concept):
        if memory_concept not in self.subconcepts:
            self.subconcepts.append(memory_concept)

    def diff_concepts(self, memory_concept):
        """
        Find the difference between this concept and another concept
        :param memory_concept:
        :return:
        """
        diff =  list(set(self.concepts) - set(memory_concept.concepts))
        return diff

    def __repr__(self):
        return self.id

##### MemoryThreads #####
class MemoryThreads:
    def __init__(self):
        # Set directories to use, creating if needed
        self.memory_dir = os.getcwd()
        self.concepts = {}

        # Load all memory files
        self.load_memory_files()

        # All pages and concepts are loaded, but not linked together. Recurse through concepts and link together
        if VERBOSE:
            print("")
            print("Recursively linking concepts")
        memory_concepts = self.concepts.values()
        for memory_concept in memory_concepts:
            self.recurse_concepts(memory_concept)
        pass

    def load_memory_files(self):
        if VERBOSE:
            print("Processing memory files")
        # Loop through all memory files
        for filename in os.listdir(self.memory_dir):
            # Only markdown files
            if not filename.endswith(".md"):
                continue
            # where the length of the filename is 39 chars (guid.md)
            if not len(filename) == 39:
                continue

            # Save memory page
            memory_file = os.path.join(self.memory_dir, filename)
            memory_page = MemoryPage(memory_file)
            memory_concept = self.get_or_create_concept(memory_page.concepts)
            memory_concept.add_page(memory_page)

    def recurse_concepts(self, main_memory_concept: MemoryConcept):
        '''
        Recurse all combinations of concepts, creating links between them
        :param main_memory_concept: memory_concept to be recursed
        :param depth: combination depth, starting with the initial number of concepts, going down to 1
        :return: None
        Recursion works from all concepts together, reducing depth each time, until each individual concept is reached.
        So for a concept list of [a, b, c, d], the function will recurse and process the combinations like:
        depth=4: [a, b, c, d]
        depth=3: [a, b, c], [a, b, d], [a, c, d], [b, c, d]. Link to [a, b, c, d]
        depth=2: [a, b], [a, c], [b, c]. Link to [a, b, c]
        depth=1: [a]. Link to [a, b]
        depth=1: [b]. Link to [a, b]
        depth=2: [a, c]. Link to [a, b, c]
        ...
        depth=2: [a, b]. Link to [a, b, d]
        ...
        '''
        # When first starting, set depth to the number of concepts minus 1
        depth = len(main_memory_concept.concepts) - 1
            #child_memory_concept = main_memory_concept
        #memory_thread = self.get_thread(concepts)
        #memory_thread.add_page(memory_page)
        if depth > 0:
            combinations = itertools.combinations(main_memory_concept.concepts, depth)
            for combination in combinations:
                sub_memory_concept = self.get_concept(list(combination))

                # Add child thread
                if sub_memory_concept:
                    sub_memory_concept.add_subconcept(main_memory_concept)

                    # Recurse while depth > 1
                    if depth > 1:
                        self.recurse_concepts(sub_memory_concept)
            pass

    def get_concept(self, concepts):
        '''
        Get MemoryConcept for set of concepts, if it already exists
        :param concepts: list of concepts
        :return: MemoryConcept, or None
        '''
        concept_hash = MemoryConcept.hash_concepts(concepts)
        if concept_hash in self.concepts:
            return self.concepts[concept_hash]
        return None

    def get_or_create_concept(self, concepts):
        '''
        Get or create a MemoryConcept for set of concepts
        :param concepts: list of concepts
        :return: MemoryConcept
        '''
        concept_hash = MemoryConcept.hash_concepts(concepts)
        if concept_hash in self.concepts:
            return self.concepts[concept_hash]

        # Create new MemoryConcept
        memory_concept = MemoryConcept(concepts)
        self.concepts[concept_hash] = memory_concept
        return memory_concept

    def write_web_markdown_files(self):
        '''
        For all concepts, write out a markdown file with sub-concepts and pages
        :return:
        '''
        if VERBOSE:
            print("")
            print("Writing concept markdown files")

        # Setup web directory
        web_directory = os.path.join(self.memory_dir, WEB_DIRECTORY)
        create_directory(web_directory)

        # Write README.md in web_directory
        readme_path = os.path.join(web_directory, "README.md")
        with open(readme_path, 'w') as readme_file:
            readme_file.write("# Memory single concepts\n")
            readme_file.write("\n")
            # Loop over concepts
            for memory_concept_hash, memory_concept in self.concepts.items():
                # Write concept into readme
                concept_path = self.get_concept_web_path(web_directory, memory_concept)
                if memory_concept.is_single:
                    concept_relative_path = os.path.relpath(concept_path, start=os.path.dirname(readme_path))
                    readme_file.write(f"* [{memory_concept.id}](./{concept_relative_path})\n")

                # Write concept markdown file
                with open(concept_path, 'w') as markdown_file:
                    print("  {}".format(concept_path))
                    markdown_file.write("# {}\n".format(' '.join(memory_concept.concepts)))
                    if memory_concept.subconcepts:
                        markdown_file.write("\n")
                        markdown_file.write("## Subconcepts\n")
                        for subconcept in memory_concept.subconcepts:
                            diff = subconcept.diff_concepts(memory_concept)
                            subconcept_path = self.get_concept_web_path(web_directory, subconcept)
                            subconcept_relative_path = os.path.relpath(subconcept_path, start=os.path.dirname(concept_path))
                            markdown_file.write(f"* [{diff[0]}](./{subconcept_relative_path})\n")

                    if memory_concept.pages:
                        markdown_file.write("\n")
                        markdown_file.write("## Pages\n")
                        for page in memory_concept.pages:
                            page_relative_path = os.path.relpath(page.filepath, start=os.path.dirname(concept_path))
                            markdown_file.write("* [{}]({})\n".format(page.title, page_relative_path))

        # Write Readme
        readme_path = os.path.join(web_directory, "README.md")

    def get_concept_web_path(self, web_directory: str, memory_concept: MemoryConcept):
        concept_name = memory_concept.id
        if type(concept_name) == bytes:
            concept_name = memory_concept.id.decode('utf-8')
        return os.path.join(web_directory, f"{concept_name}.md")

    def create_symlinks(self):
        """
        Create web of concepts using symlinks for easy local editing
        :return:
        """
        if VERBOSE:
            print("")
            print("Creating concept symlinks")

        # Setup symlink directory
        symlink_directory = os.path.join(self.memory_dir, SYMLINK_DIRECTORY)
        create_directory(symlink_directory)

        # Save list of current files so we can clean up old files later (as dictionary with filenames as keys)
        old_files = search_files(symlink_directory)

        # Sort concepts by how may concepts they have
        concept_values = list(self.concepts.values())
        concept_values.sort(key = lambda i: len(i.concepts))

        # Loop over concepts
        for memory_concept in concept_values:
            # Create directory for concept
            concept_directory = os.path.join(symlink_directory, memory_concept.id)
            create_directory(concept_directory) # create if not exists

            # Remove from old_list
            with suppress(ValueError):
                old_files.remove(concept_directory)

            # Create directories for subconcepts and link
            if memory_concept.subconcepts:
                for subconcept in memory_concept.subconcepts:
                    diff = subconcept.diff_concepts(memory_concept)
                    subconcept_path = os.path.join(symlink_directory, subconcept.id) #
                    subconcept_relative_path = f"../{subconcept.id}"
                    subconcept_symlink_name = os.path.join(concept_directory, diff[0]) # Uses the diff as the symlink name to the folder
                    create_directory(subconcept_path)  # create if not exists
                    create_symlink(subconcept_symlink_name, subconcept_relative_path)
                    pass

            # Create symlinks for pages
            if memory_concept.pages:
                for page in memory_concept.pages:
                    # Create file symlink using relative paths
                    title = page.title.replace('*', '')
                    concept_symlink_path = os.path.join(concept_directory, f"{title}.md")
                    concept_relative_path = os.path.relpath(page.filepath, start=concept_directory)
                    create_symlink(concept_symlink_path, concept_relative_path)

                    # Remove from old_list
                    with suppress(ValueError):
                        old_files.remove(concept_symlink_path)

        # Clean up old files, sorting list by length decending to delete files before folders
        old_files.sort(key=lambda i: len(i), reverse=True)
        for filename in old_files:
            if os.path.islink(filename):
                os.remove(filename)
            elif os.path.isdir(filename):
                if len(os.listdir(filename)) == 0:  # Check if the folder is empty
                    shutil.rmtree(filename)  # If so, delete it
        pass

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

##### Typer #####
app = typer.Typer()

@app.command("guid")
def app_guid(
        verbose: bool = typer.Option(True, help="Verbose output")
):
    """
    Copy a random guid to the clipboard.
    """
    guid = str(uuid.uuid4())
    copy_to_clipboard(guid)
    if verbose:
        pretty_guid = typer.style(guid, fg=typer.colors.GREEN, bold=True)
        typer.echo(f"{pretty_guid} copied to clipboard")

@app.command("create")
def app_create(
        open_file: bool = typer.Option(True, "--open", help="Open the memory after creating"),
        verbose: bool = typer.Option(True, help="Verbose output")
):
    """
    Create a new memory.
    """
    while True:
        guid = str(uuid.uuid4())
        filename = f"{guid}.md"
        if not os.path.exists(filename):
            break
    if verbose:
        typer.echo("Creating new memory "+typer.style(filename, fg=typer.colors.GREEN, bold=True))
    with open(filename, 'w') as fp:
        pass
    if open_file:
        open_file_in_editor(filename)

@app.command("open")
def app_open(
        filename: str = typer.Argument("World", help="Filename to open"),
        verbose: bool = typer.Option(True, help="Verbose output")
):
    """
    Open an existing memory.
    """
    if not os.path.exists(filename):
        typer.echo("File does not exist.")
        raise typer.Exit(code=1)
    if verbose:
        typer.echo("Opening "+typer.style(filename, fg=typer.colors.GREEN, bold=True))
    open_file_in_editor(filename)

@app.command("web")
def app_web(
    verbose: bool = typer.Option(True, help="Verbose output")
):
    """
    Create web concept threads for memories
    """
    VERBOSE = verbose
    threads = MemoryThreads()
    threads.write_web_markdown_files()
    pass

@app.command("symlink")
def app_symlink(
    verbose: bool = typer.Option(True, help="Verbose output")
):
    """
    Create symlink concept web
    """
    VERBOSE = verbose
    threads = MemoryThreads()
    threads.create_symlinks()
    pass

##### Main #####
if __name__ == "__main__":
    app()