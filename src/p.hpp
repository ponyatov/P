#ifndef P_H
#define P_H

#include <iostream>
#include <sstream>
#include <locale>
#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
using namespace std;

#include <QApplication>
#include <QString>

// \ metal

class Object {
        QString value;
    public:
        Object(const char* V);
        QString dump(int depth=0, QString prefix="");
};
// / metal
#endif // P_H
