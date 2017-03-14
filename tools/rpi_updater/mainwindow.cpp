#include "mainwindow.h"
#include "ui_mainwindow.h"

#include <QDebug>
#include <QString>
#include <QDirIterator>
#include <QTreeWidget>
#include <QSet>
#include <QPersistentModelIndex>
#include <QProcess>

#include <fileselector.h>

#include <cstdlib>

// TODO: set into a textbox of the UI
#define RPI_IP  "192.168.1.65"
#define RPI_USER    "pi"
#define RPI_FOLDER  "/tfg"

MainWindow::MainWindow(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::MainWindow)
{
    ui->setupUi(this);

    std::string pathStr(std::getenv("HOME"));
    pathStr += "/workspaces/IPoL.git/trunk/";

    fileSelector_ = new FileSelector(pathStr.c_str(), this);

    ui->fileTree_->setModel(fileSelector_);
    ui->fileTree_->setRootIndex(fileSelector_->index("/home/ubuntuk/workspaces/IPoL.git/trunk/"));
}

MainWindow::~MainWindow()
{
    delete ui;
}

void MainWindow::on_updateBtn__clicked()
{
    std::vector<std::string> toSync;

    QSet<QPersistentModelIndex> *checked = fileSelector_->getToSyncList();
    QSet<QPersistentModelIndex>::iterator it;
    for(it = checked->begin(); it != checked->end(); it++)
    {
        std::string fileToAdd = fileSelector_->filePath(*it).toStdString();
        //if(fileSelector_->isDir(*it)) fileToAdd += "/";
        toSync.push_back(fileToAdd);
    }

    syncFiles(toSync);
}

void MainWindow::syncFiles(std::vector<std::string> toSync)
{
    std::string pathStr(std::getenv("HOME"));
    pathStr += "/workspaces/IPoL.git/trunk/";
    std::string::size_type size = pathStr.length();

    for(unsigned int i = 0; i < toSync.size(); i++)
    {
        // get the file relative to trunk/
        std::string destFolder = toSync[i];
        destFolder.erase(0, size);

        // create string with rsync command
        std::string rsync = "/bin/bash -c \"rsync -aR "; // -R to maintain the directory structure
        rsync += pathStr;
        rsync += "./";
        rsync += destFolder;
        rsync += " ";
        rsync += RPI_USER;
        rsync += "@";
        rsync += RPI_IP;
        rsync += ":";
        rsync += RPI_FOLDER;
        rsync += " \"";
        //qInfo() << QString::fromStdString(rsync);

        // Execute rsync command
        QProcess process;
        process.start(QString::fromStdString(rsync));
        process.waitForFinished(-1);
        QByteArray error = process.readAllStandardError();
        qDebug() << error;
    }
}

