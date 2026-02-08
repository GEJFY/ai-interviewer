/**
 * Tasks list screen.
 */

import { View, Text, StyleSheet, FlatList, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface Task {
  id: string;
  title: string;
  project: string;
  deadline: string;
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'in_progress' | 'completed';
}

const mockTasks: Task[] = [
  {
    id: '1',
    title: '経理部インタビュー実施',
    project: '内部統制評価プロジェクト',
    deadline: '2024-01-16',
    priority: 'high',
    status: 'pending',
  },
  {
    id: '2',
    title: '業務記述書レビュー',
    project: '内部統制評価プロジェクト',
    deadline: '2024-01-18',
    priority: 'medium',
    status: 'in_progress',
  },
  {
    id: '3',
    title: 'RCM作成',
    project: '内部統制評価プロジェクト',
    deadline: '2024-01-20',
    priority: 'low',
    status: 'pending',
  },
];

const priorityConfig = {
  high: { label: '高', color: '#ef4444' },
  medium: { label: '中', color: '#f59e0b' },
  low: { label: '低', color: '#22c55e' },
};

const statusConfig = {
  pending: { label: '未着手', icon: 'ellipse-outline' as const },
  in_progress: { label: '進行中', icon: 'time' as const },
  completed: { label: '完了', icon: 'checkmark-circle' as const },
};

export default function TasksScreen() {
  const renderItem = ({ item }: { item: Task }) => {
    const priority = priorityConfig[item.priority];
    const status = statusConfig[item.status];

    return (
      <TouchableOpacity style={styles.card}>
        <View style={styles.cardLeft}>
          <Ionicons
            name={status.icon}
            size={24}
            color={item.status === 'completed' ? '#22c55e' : '#9ca3af'}
          />
        </View>

        <View style={styles.cardContent}>
          <Text style={styles.title}>{item.title}</Text>
          <Text style={styles.project}>{item.project}</Text>

          <View style={styles.metaRow}>
            <View style={styles.metaItem}>
              <Ionicons name="calendar-outline" size={14} color="#6b7280" />
              <Text style={styles.metaText}>{item.deadline}</Text>
            </View>
            <View style={[styles.priorityBadge, { backgroundColor: `${priority.color}20` }]}>
              <Text style={[styles.priorityText, { color: priority.color }]}>
                {priority.label}
              </Text>
            </View>
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  const pendingTasks = mockTasks.filter(t => t.status !== 'completed');
  const completedTasks = mockTasks.filter(t => t.status === 'completed');

  return (
    <View style={styles.container}>
      <FlatList
        data={pendingTasks}
        renderItem={renderItem}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        ListHeaderComponent={
          <Text style={styles.sectionTitle}>
            未完了タスク ({pendingTasks.length})
          </Text>
        }
        ListFooterComponent={
          completedTasks.length > 0 ? (
            <View>
              <Text style={styles.sectionTitle}>
                完了済み ({completedTasks.length})
              </Text>
              {completedTasks.map(task => (
                <View key={task.id} style={[styles.card, styles.completedCard]}>
                  <View style={styles.cardLeft}>
                    <Ionicons name="checkmark-circle" size={24} color="#22c55e" />
                  </View>
                  <View style={styles.cardContent}>
                    <Text style={[styles.title, styles.completedText]}>{task.title}</Text>
                  </View>
                </View>
              ))}
            </View>
          ) : null
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f3f4f6',
  },
  list: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6b7280',
    marginBottom: 12,
    marginTop: 8,
  },
  card: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  completedCard: {
    opacity: 0.6,
  },
  cardLeft: {
    marginRight: 12,
    justifyContent: 'flex-start',
    paddingTop: 2,
  },
  cardContent: {
    flex: 1,
  },
  title: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1f2937',
    marginBottom: 4,
  },
  completedText: {
    textDecorationLine: 'line-through',
    color: '#9ca3af',
  },
  project: {
    fontSize: 13,
    color: '#6b7280',
    marginBottom: 8,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  metaText: {
    fontSize: 12,
    color: '#6b7280',
    marginLeft: 4,
  },
  priorityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  priorityText: {
    fontSize: 11,
    fontWeight: '600',
  },
});
