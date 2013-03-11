
#include <getopt.h>
#include <iostream>
#include <fstream>

#include <binpac++.h>
#include <hilti.h>
#include <util.h>

using namespace std;

const char* Name = "binpac";

bool dump_ast = false;
bool cfg = false;
bool output_binpac = false;
bool output_llvm = false;
bool add_stdlibs = false;

string output = "/dev/stdout";

static struct option long_options[] = {
    { "ast",     no_argument, 0, 'A' },
    { "debug",   no_argument, 0, 'd' },
    { "cgdebug", no_argument, 0, 'D' },
    { "help",    no_argument, 0, 'h' },
    { "print",   no_argument, 0, 'p' },
    { "print-always",   no_argument, 0, 'W' },
    { "cfg",   no_argument, 0, 'c' },
    { "prototypes", no_argument, 0, 'P' },
    { "output",  required_argument, 0, 'o' },
    { "version", no_argument, 0, 'v' },
    { "llvm", no_argument, 0, 'l' },
    { "optimize", no_argument, 0, 'O' },
    { "add-stdlibs", no_argument, 0, 's' },
    { 0, 0, 0, 0 }
};

void usage()
{
    auto dbglist = binpac::Options().cgDebugLabels();
    auto dbgstr = util::strjoin(dbglist.begin(), dbglist.end(), "/");

    cerr << "Usage: " << Name << " [options] <input.pac2>\n"
            "\n"
            "Options:\n"
            "\n"
            "  -A | --ast            Dump intermediary ASTs to stderr.\n"
            "  -c | --cfg            When outputting HILTI code, include control/data flow information.\n"
            "  -d | --debug          Debug level for the generated code. Each time increases level. [Default: 0]\n"
            "  -D | --cgdebug <type> Debug output during code generation; type can be " << dbgstr << ".\n"
            "  -h | --help           Print usage information.\n"
            "  -I | --import <dir>   Add directory to import path.\n"
            "  -n | --no-validate    Do not validate resulting BinPAC++ or HILTI ASTs (for debugging only).\n"
            "  -o | --output <file>  Specify output file.                    [Default: stdout].\n"
            "  -p | --print          Just output all parsed BinPAC++ code again.\n"
            "  -W | --print-always   Like -p, but don't verify correctness first.\n"
            "  -l | --llvm           Output the final LLVM code.\n"
            "  -O | --optimize       Optimize generated code (for -l         [Default: off].\n"
            "  -s | --add-stdlibs    Add standard HILTI runtime libraries (for -l).\n"
            "\n";
}

void version()
{
    cerr << Name << " v" << binpac::version() << endl;
}

void error(const string& file, const string& msg)
{
    if ( file.size() )
        cerr << util::basename(file) << ": ";

    cerr << msg << endl;
    exit(1);
}

int main(int argc, char** argv)
{
    binpac::Options options;

    while ( true ) {
        int c = getopt_long(argc, argv, "AcdD:o:nOWlspI:vh", long_options, 0);

        if ( c < 0 )
            break;

        switch (c) {
         case 'A':
            dump_ast = true;
            break;

         case 'c':
            cfg = true;
            break;

         case 'd':
            options.debug = true;
            break;

         case 'D':
            options.cg_debug.insert(optarg);
            break;

         case 'o':
            output = optarg;
            break;

         case 'n':
            options.verify = true;
            break;

         case 'W':
            output_binpac = true;
            options.verify = false;
            break;

         case 'p':
            output_binpac = true;
            break;

         case 'l':
            output_llvm = true;
            break;

         case 's':
            add_stdlibs = true;
            break;

         case 'O':
            options.optimize = true;
            break;

         case 'I':
            options.libdirs_pac2.push_back(optarg);
            break;

         case 'v':
            ::version();
            return 0;

         case 'h':
            usage();
            return 0;

         default:
            usage();
            return 1;
        }

    }

    if ( optind == argc )
        error("", "No input file given.");

    if ( optind - argc > 1 )
        error("", "Two many input file given.");

    string input = argv[optind];

    ofstream out;
    out.open(output, ios::out | ios::trunc);

    if ( ! out.good() )
        error(output, "Cannot open file for output.");

    hilti::init();
    binpac::init();

    auto ctx = std::make_shared<binpac::CompilerContext>(options);

    auto module = ctx->load(input);

    if ( ! module ) {
        error(input, "Aborting due to input error.");
        return 1;
    }

    if ( dump_ast ) {
        ctx->dump(module, cerr);
        cerr << std::endl;
    }

    if ( output_binpac )
        return ctx->print(module, out);

    auto hilti_module = ctx->compile(module);

    if ( ! hilti_module ) {
        error(input, "Aborting due to compilation error.");
        return 1;
    }

    if ( dump_ast ) {
        hilti_module->dump(cerr);
        cerr << std::endl;
    }

    if ( ctx->options().cgDebugging("scopes") ) {
        hilti::passes::ScopePrinter scope_printer(cerr);

        if ( ! scope_printer.run(hilti_module) )
            return 1;
    }

    if ( output_llvm ) {
        std::list<shared_ptr<hilti::Module>> mods = { hilti_module };
        auto llvm_module = ctx->linkModules(input, mods,
                                            std::list<string>(),
                                            path_list(), path_list(),
                                            false, add_stdlibs);

        if ( ! llvm_module ) {
            error(input, "Aborting due to link error.");
            return 1;
        }

        if ( ! ctx->hiltiContext()->printBitcode(llvm_module, std::cout) ) {
            error(input, "Aborting due to LLVM problem.");
            return 1;
        }

        return 0;
    }

    if ( ! ctx->hiltiContext()->print(hilti_module, out, cfg) ) {
        error(input, "Aborting due to HILTI printer error.");
        return 1;
    }

    return 0;
}
