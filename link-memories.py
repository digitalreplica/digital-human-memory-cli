import itertools
import os

MEMORY_DIR = 'memory'
THREAD_DIR = 'threads'
MULTI_THREAD_DIR = '.threads'

def remove_hash_from_tags(input):
    return input.replace('#', '')

def create_directory(dir):
    '''
    Creates a directory, if it doesn't exist
    :param dir:
    :return:
    '''
    if not os.path.isdir(dir):
        print(" Making {}".format(dir))
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


def recurse_thread_combinations(memory_file, memory_title, threads, depth, dest_dir):
    '''
    Creates all combininations of paths to file.
    - ./threads contains top level (single) threads
    - ./.thread (hidden) contains combinations of threads, each a folder like tag1-tag2-tag3
    - inside folders are simlinks to nested threads. So inside tag1-tag2 is a symlink called tag3 pointing to tag1-tag2-tag3
    :param memory_file:
    :param memory_title:
    :param threads:
    :param depth:
    :param dest_dir:
    :return:
    '''
    global MEMORY_DIR, THREAD_DIR, MULTI_THREAD_DIR

    # Determine base_path to create folder in, and the target relative path for the symlink
    # Top-level threads hop from threads to .threads, everything else stays within .threads
    if depth > 1:
        base_path = os.path.join(dest_dir, MULTI_THREAD_DIR)
        relative_path = '../../'
        memory_relative_path = '../../'+MEMORY_DIR
    else:
        base_path = os.path.join(dest_dir, THREAD_DIR)
        relative_path = '../../' + MULTI_THREAD_DIR
        memory_relative_path = '../../' + MEMORY_DIR
    target_relative_path = os.path.join(relative_path, '-'.join(threads))

    # Create a threads_set for easy set diffing
    threads_set = set(threads)

    # Loop over all combinations at our current depth
    spaces = ' '*(4-depth)
    combinations = itertools.combinations(threads, depth)
    for combination in combinations:
        # Create directory that joins multiple threads. Ex: ./.threads/tag1-tag2-tag3
        path = os.path.join(base_path, '-'.join(combination))
        create_directory(path)

        # Create a symlink to the file
        symlink_file = os.path.join(path, memory_title+".md")
        symlink_file_target = os.path.join(memory_relative_path, memory_file)
        create_symlink(symlink_file, symlink_file_target)

        # Create a symlink for a path to a deeper nested thread
        diff = list(threads_set - set(combination))
        if diff:
            print("{}{}: {} -> {}".format(spaces, path, diff[0], target_relative_path))
            symlink_path = os.path.join(path, diff[0])
            create_symlink(symlink_path, target_relative_path)
        else:
            print("{}".format(path))
        if depth > 1:
            recurse_thread_combinations(memory_file, memory_title, combination, depth-1, dest_dir)



def create_threads_for_repo(repo_dir, dest_dir):
    # Set directories to use, creating if needed
    memory_dir = os.path.join(repo_dir, MEMORY_DIR)
    thread_dir = os.path.join(dest_dir, THREAD_DIR)
    create_directory(thread_dir)
    multi_thread_dir = os.path.join(dest_dir, MULTI_THREAD_DIR)
    create_directory(multi_thread_dir)

    # Loop through all memory files
    for filename in os.listdir(memory_dir):
        # Only markdown files
        if not filename.endswith(".md"):
            continue

        memory_file = os.path.join(memory_dir, filename)
        print("Processing {}".format(memory_file))
        with open(memory_file) as f:
            # Read first two lines to extract title and thread names
            memory_title = f.readline().rstrip().replace('# ', '')
            #print(title)
            threads = []
            thread_line = f.readline().rstrip()
            if thread_line.startswith("#"):
                # Make sure we have tags on second line.
                thread_lines = thread_line.split(' ')
                threads = list(map(remove_hash_from_tags, thread_lines))
                threads.sort()
            recurse_thread_combinations(filename, memory_title, threads, len(threads), dest_dir)

            # skip
            continue
            for thread in threads:
                print(" {}".format(thread))
                # Make main thread
                main_thread_directory = os.path.join(main_directory, thread)

                # Symlink file
                main_thread_file = os.path.join(main_thread_directory, title + ".md")

print(os.getcwd())
create_threads_for_repo('.', '.')
