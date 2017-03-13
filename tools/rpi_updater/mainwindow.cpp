#include "mainwindow.h"
#include "ui_mainwindow.h"

#include <QDebug>
#include <QString>
#include <QDirIterator>

#include <boost/filesystem.hpp>
#include <cstdlib>

MainWindow::MainWindow(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::MainWindow)
{
    ui->setupUi(this);

    listDirectoryTree();
}

MainWindow::~MainWindow()
{
    delete ui;
}

void MainWindow::listDirectoryTree()
{
    std::string pathStr(std::getenv("HOME"));
    pathStr += "/workspaces/IPoL.git/trunk/";
/*
    using namespace boost::filesystem;
    path p(pathStr.c_str());
    recursive_directory_iterator dir(p), end;

    while(dir != end)
    {
//        if (dir->path().filename() == exclude_this_directory)
//        {
//            dir.no_push(); // don't recurse into this directory.
//        }
        qInfo() << QString::fromStdString(dir->path().string());
        ++dir;
    } */

    if(!QDir(QString::fromStdString(pathStr)).exists()) qInfo() << "Does not exist";
    else
    {
        QDirIterator it(pathStr.c_str(), QDirIterator::Subdirectories);
        while(it.hasNext())
        {
            if(it.fileName() != QString::fromStdString(".") && it.fileName() != QString::fromStdString(".."))
            {
                qInfo() << it.filePath();
            }
            it.next();
        }
    }
}
