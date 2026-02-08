/**
 * Interviews list screen.
 */

import { View, Text, StyleSheet, FlatList, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

interface Interview {
  id: string;
  title: string;
  interviewee: string;
  date: string;
  status: 'scheduled' | 'in_progress' | 'completed';
  duration?: number;
}

const mockInterviews: Interview[] = [
  {
    id: '1',
    title: '月次決算プロセス',
    interviewee: '経理部 山田様',
    date: '2024-01-15 14:00',
    status: 'scheduled',
  },
  {
    id: '2',
    title: '購買承認フロー',
    interviewee: '購買部 佐藤様',
    date: '2024-01-14 10:00',
    status: 'completed',
    duration: 45,
  },
  {
    id: '3',
    title: '売上計上プロセス',
    interviewee: '営業部 田中様',
    date: '2024-01-13 15:00',
    status: 'completed',
    duration: 60,
  },
];

const statusConfig = {
  scheduled: { label: '予定', color: '#3b82f6', icon: 'time' as const },
  in_progress: { label: '実施中', color: '#f59e0b', icon: 'play-circle' as const },
  completed: { label: '完了', color: '#10b981', icon: 'checkmark-circle' as const },
};

export default function InterviewsScreen() {
  const router = useRouter();

  const renderItem = ({ item }: { item: Interview }) => {
    const status = statusConfig[item.status];

    return (
      <TouchableOpacity
        style={styles.card}
        onPress={() => router.push(`/interview/${item.id}`)}
      >
        <View style={styles.cardHeader}>
          <Text style={styles.title}>{item.title}</Text>
          <View style={[styles.statusBadge, { backgroundColor: `${status.color}20` }]}>
            <Ionicons name={status.icon} size={14} color={status.color} />
            <Text style={[styles.statusText, { color: status.color }]}>
              {status.label}
            </Text>
          </View>
        </View>

        <View style={styles.cardBody}>
          <View style={styles.infoRow}>
            <Ionicons name="person" size={16} color="#6b7280" />
            <Text style={styles.infoText}>{item.interviewee}</Text>
          </View>
          <View style={styles.infoRow}>
            <Ionicons name="calendar" size={16} color="#6b7280" />
            <Text style={styles.infoText}>{item.date}</Text>
          </View>
          {item.duration && (
            <View style={styles.infoRow}>
              <Ionicons name="time" size={16} color="#6b7280" />
              <Text style={styles.infoText}>{item.duration}分</Text>
            </View>
          )}
        </View>

        <View style={styles.cardFooter}>
          {item.status === 'scheduled' && (
            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => router.push(`/interview/${item.id}`)}
            >
              <Ionicons name="play" size={16} color="#fff" />
              <Text style={styles.actionButtonText}>開始</Text>
            </TouchableOpacity>
          )}
          {item.status === 'completed' && (
            <TouchableOpacity style={styles.secondaryButton}>
              <Ionicons name="document-text" size={16} color="#2563eb" />
              <Text style={styles.secondaryButtonText}>レポート</Text>
            </TouchableOpacity>
          )}
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <FlatList
        data={mockInterviews}
        renderItem={renderItem}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        ListHeaderComponent={
          <TouchableOpacity style={styles.newButton}>
            <Ionicons name="add-circle" size={20} color="#fff" />
            <Text style={styles.newButtonText}>新規インタビュー</Text>
          </TouchableOpacity>
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
  newButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#2563eb',
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
  },
  newButtonText: {
    color: '#fff',
    fontWeight: '600',
    marginLeft: 8,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
    flex: 1,
    marginRight: 8,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '500',
    marginLeft: 4,
  },
  cardBody: {
    marginBottom: 12,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  infoText: {
    fontSize: 14,
    color: '#6b7280',
    marginLeft: 8,
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
    paddingTop: 12,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2563eb',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  actionButtonText: {
    color: '#fff',
    fontWeight: '500',
    marginLeft: 6,
  },
  secondaryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#2563eb',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  secondaryButtonText: {
    color: '#2563eb',
    fontWeight: '500',
    marginLeft: 6,
  },
});
