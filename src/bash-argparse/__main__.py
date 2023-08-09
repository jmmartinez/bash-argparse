if __name__ == "__main__":
    try:
        from core import main
    except ImportError:
        from importlib import __import__
        main = __import__("bash-argparse.core").core.main
    main()
