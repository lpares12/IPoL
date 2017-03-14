#include "fileselector.h"

#include <QDebug>

FileSelector::FileSelector(const char *rootPath, QObject *parent) : parent_(parent)
{
    this->setRootPath(rootPath);
}

FileSelector::~FileSelector()
{
    checklist_.clear();
}

bool FileSelector::setData(const QModelIndex& index, const QVariant& value, int role)
{
    if (role == Qt::CheckStateRole && index.column() == 0) {
        QModelIndexList list;
        getAllChildren(index, list);
        if(value == Qt::Checked)
        {
            toSync_.insert(index);
            for(int i = 0; i < list.size(); i++)
            {
                checklist_.insert(list[i]);
                emit dataChanged(list[i], list[i]);
            }
        }
        else if(value == Qt::Unchecked)
        {
            toSync_.remove(index);
            for(int i = 0; i < list.size(); i++)
            {
                checklist_.remove(list[i]);
                emit dataChanged(list[i], list[i]);
            }
        }
        return true;
    }
    return QFileSystemModel::setData(index, value, role);
}

Qt::ItemFlags FileSelector::flags(const QModelIndex& index) const
{
    return QFileSystemModel::flags(index) | Qt::ItemIsUserCheckable;
}

QVariant FileSelector::data(const QModelIndex& index, int role) const
{
    if (role == Qt::CheckStateRole && index.column() == 0) {
        if(checklist_.contains(index)) return Qt::Checked;
        else return Qt::Unchecked;
    }
    return QFileSystemModel::data(index, role);
}

QSet<QPersistentModelIndex>* FileSelector::getToSyncList()
{
    return &toSync_;
}

void FileSelector::getAllChildren(const QModelIndex &index, QModelIndexList &indices)
{
    //qInfo() << QString::fromStdString(filePath(index).toStdString());
    indices.push_back(index);
    for(int i = 0; i != rowCount(index); i++) getAllChildren(index.child(i,0), indices);
}
