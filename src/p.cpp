#include <p.hpp>

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);
    cout << (new Object("Hello"))->dump() << endl;
    return app.exec();
}

Object::Object(const char *V) { value = QString(V); }

QString Object::dump(int depth, QString prefix) {
    cout << "\n<" << value << ">\n";
}
