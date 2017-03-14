#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>

#include <vector>

// todo: remove
#include <QDir>
//

#include "fileselector.h"

namespace Ui {
class MainWindow;
}

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = 0);
    ~MainWindow();

private slots:
    void on_updateBtn__clicked();

private:
    Ui::MainWindow *ui;

    FileSelector *fileSelector_;

    std::vector<QDir> listDirectoryTree();
    void syncFiles(std::vector<std::string> toSync);
};

#endif // MAINWINDOW_H
