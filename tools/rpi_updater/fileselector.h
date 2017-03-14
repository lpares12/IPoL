#ifndef FILESELECTOR_H
#define FILESELECTOR_H

#include <QModelIndex>
#include <QModelIndexList>
#include <QVariant>
#include <QFileSystemModel>
#include <QSet>
#include <QPersistentModelIndex>

class FileSelector : public QFileSystemModel
{
public:
    FileSelector(const char *rootPath, QObject *parent = nullptr);
    ~FileSelector();

    QSet<QPersistentModelIndex> *getToSyncList();

    bool setData(const QModelIndex& index, const QVariant& value, int role);
    Qt::ItemFlags flags(const QModelIndex& index) const;
    QVariant data(const QModelIndex& index, int role) const;

private:
    QObject *parent_;
    QSet<QPersistentModelIndex> checklist_;
    QSet<QPersistentModelIndex> toSync_;

    void getAllChildren(const QModelIndex &index, QModelIndexList &indices);
};

#endif // FILESELECTOR_H
